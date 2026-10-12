"""Canary vs stable analysis for a KServe InferenceService canary step.

Used between ``canaryTrafficPercent`` steps (10% -> 50% -> 100%) in
``deploy-canary``. Observes the canary for ``--window`` and polls every
``--interval``; fails fast on any breach once ``--min-requests`` canary
requests have been seen.

Checks (canary revision vs stable/previous revision):

* 5xx error rate          <= ``--max-error-rate``
* p99 latency             <= ``--max-p99-ms`` and <= stable p99 x (1 + ``--max-p99-regression``)
* score-distribution PSI  <= ``--max-score-psi`` (canary vs stable ``churn_score`` histogram)

Metric sources (Azure Monitor managed Prometheus):

* Istio ``istio_requests_total`` / ``istio_request_duration_milliseconds_bucket``
  with ``destination_workload="<knative-revision>-deployment"``
* ``churn_score_bucket{revision=...}`` histogram exported by the KServe
  transformer (``serving/churn_serving/transformer.py``, labelled with ``K_REVISION``)

Revisions are read from ``status.components.<component>.traffic`` of the
InferenceService via ``kubectl`` unless ``--canary-revision`` /
``--stable-revision`` are given. ``--input-json`` evaluates a pre-collected
snapshot instead (offline / tests).

Exit codes: 0 = promote, 1 = rollback (threshold breached),
2 = inconclusive (insufficient traffic, missing metrics, query errors).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404
import sys
import time
from collections.abc import Callable
from typing import Any

from churn.deploy.common import (
    EXIT_FAIL,
    EXIT_INCONCLUSIVE,
    EXIT_PASS,
    PrometheusClient,
    append_file,
    cumulative_to_bins,
    observe,
    parse_duration,
    promql_duration,
    psi,
    render,
)


def resolve_revisions(isvc: str, namespace: str, component: str) -> tuple[str, str]:
    """Return (canary_revision, stable_revision) from the InferenceService status."""
    kubectl = shutil.which("kubectl")
    if not kubectl:
        raise RuntimeError("kubectl not found; pass --canary-revision/--stable-revision")
    out = subprocess.run(  # nosec B603
        [kubectl, "get", "isvc", isvc, "-n", namespace, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return revisions_from_status(json.loads(out), component)


def revisions_from_status(isvc: dict[str, Any], component: str) -> tuple[str, str]:
    comp = (isvc.get("status") or {}).get("components", {}).get(component) or {}
    canary = stable = None
    for t in comp.get("traffic") or []:
        if t.get("latestRevision") or t.get("tag") == "latest":
            canary = canary or t.get("revisionName")
        elif t.get("tag") == "prev" or not t.get("latestRevision", True):
            stable = stable or t.get("revisionName")
    canary = canary or comp.get("latestReadyRevision") or comp.get("latestCreatedRevision")
    stable = stable or comp.get("previousRolledoutRevision")
    if not canary or not stable or canary == stable:
        raise RuntimeError(
            f"cannot determine distinct canary/stable revisions for component '{component}'"
        )
    return canary, stable


def collect(prom: PrometheusClient, namespace: str, revision: str, window_s: int) -> dict:
    w = promql_duration(window_s)
    sel = (
        f'reporter="destination",destination_workload_namespace="{namespace}",'
        f'destination_workload="{revision}-deployment"'
    )
    total = prom.scalar(f"sum(increase(istio_requests_total{{{sel}}}[{w}]))")
    errors = prom.scalar(f'sum(increase(istio_requests_total{{{sel},response_code=~"5.."}}[{w}]))')
    p99 = prom.scalar(
        "histogram_quantile(0.99, sum by (le) "
        f"(rate(istio_request_duration_milliseconds_bucket{{{sel}}}[{w}])))"
    )
    hist = prom.histogram(
        f'sum by (le) (increase(churn_score_bucket{{namespace="{namespace}",'
        f'revision="{revision}"}}[{w}]))'
    )
    return {
        "revision": revision,
        "requests": total,
        "error_rate": None if not total else (errors or 0.0) / total,
        "p99_ms": p99,
        "score_hist": {str(k): v for k, v in hist.items()},
    }


def _bins(snapshot: dict) -> list[float] | None:
    hist = snapshot.get("score_hist") or {}
    if not hist:
        return None
    return cumulative_to_bins({float(k): float(v) for k, v in hist.items()})


def evaluate(canary: dict, stable: dict, args: argparse.Namespace) -> tuple[int, list[dict]]:
    """Return (exit_code, checks) for one snapshot."""
    checks: list[dict] = []

    def check(name: str, actual: float | None, limit: float | None, ok: bool | None) -> None:
        checks.append({"check": name, "actual": actual, "limit": limit, "ok": ok})

    requests = canary.get("requests") or 0.0
    check("canary_requests", requests, args.min_requests, requests >= args.min_requests)

    err = canary.get("error_rate")
    check(
        "error_rate", err, args.max_error_rate, None if err is None else err <= args.max_error_rate
    )

    p99 = canary.get("p99_ms")
    check("p99_ms", p99, args.max_p99_ms, None if p99 is None else p99 <= args.max_p99_ms)
    stable_p99 = stable.get("p99_ms")
    if p99 is not None and stable_p99:
        limit = stable_p99 * (1 + args.max_p99_regression)
        check("p99_regression_vs_stable", p99, limit, p99 <= limit)

    c_bins, s_bins = _bins(canary), _bins(stable)
    score_psi = None
    if c_bins and s_bins and len(c_bins) == len(s_bins) and sum(c_bins) and sum(s_bins):
        score_psi = psi(s_bins, c_bins)
    check(
        "score_psi",
        score_psi,
        args.max_score_psi,
        None if score_psi is None else score_psi <= args.max_score_psi,
    )

    enough = requests >= args.min_requests
    if enough and any(c["ok"] is False for c in checks):
        return EXIT_FAIL, checks
    if not enough or any(c["ok"] is None for c in checks):
        return EXIT_INCONCLUSIVE, checks
    return EXIT_PASS, checks


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m churn.deploy.canary_analysis", description=__doc__)
    p.add_argument("--prometheus-url", help="managed Prometheus query endpoint")
    p.add_argument("--namespace", default="churn-serving")
    p.add_argument("--isvc", default="churn-lgbm")
    p.add_argument("--component", default="transformer", choices=["transformer", "predictor"])
    p.add_argument("--canary-revision")
    p.add_argument("--stable-revision")
    p.add_argument("--window", default="30m", help="observation window, e.g. 30m")
    p.add_argument("--interval", default="60s", help="poll interval")
    p.add_argument("--max-p99-ms", type=float, required=True)
    p.add_argument("--max-p99-regression", type=float, default=0.25)
    p.add_argument("--max-error-rate", type=float, required=True)
    p.add_argument("--max-score-psi", type=float, required=True)
    p.add_argument("--min-requests", type=float, default=200)
    p.add_argument("--input-json", help="evaluate a pre-collected {canary, stable} snapshot")
    p.add_argument("--output", help="write the decision JSON here")
    p.add_argument("--summary", help="markdown summary file (default $GITHUB_STEP_SUMMARY)")
    return p


def run(
    args: argparse.Namespace,
    prom: PrometheusClient | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[int, list[dict]]:
    if args.input_json:
        with open(args.input_json) as fh:
            snap = json.load(fh)
        return evaluate(snap["canary"], snap["stable"], args)

    if not args.prometheus_url and prom is None:
        raise ValueError("--prometheus-url is required unless --input-json is given")
    prom = prom or PrometheusClient(args.prometheus_url)
    if args.canary_revision and args.stable_revision:
        canary_rev, stable_rev = args.canary_revision, args.stable_revision
    else:
        canary_rev, stable_rev = resolve_revisions(args.isvc, args.namespace, args.component)
    print(f"canary revision={canary_rev} stable revision={stable_rev}")

    def step(lookback: int) -> tuple[int, list[dict]]:
        canary = collect(prom, args.namespace, canary_rev, lookback)
        stable = collect(prom, args.namespace, stable_rev, lookback)
        return evaluate(canary, stable, args)

    return observe(parse_duration(args.window), parse_duration(args.interval), step, clock, sleep)


def main(argv: list[str] | None = None, **kwargs: Any) -> int:
    args = build_parser().parse_args(argv)
    try:
        code, checks = run(args, **kwargs)
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: canary analysis could not run: {exc}", file=sys.stderr)
        return EXIT_INCONCLUSIVE
    report = render(code, checks, f"Canary analysis {args.isvc} ({args.window})")
    print(report)
    append_file(args.summary or os.environ.get("GITHUB_STEP_SUMMARY"), report)
    if args.output:
        with open(args.output, "w") as fh:
            json.dump({"exit_code": code, "checks": checks}, fh, indent=2)
    return code


if __name__ == "__main__":
    sys.exit(main())
