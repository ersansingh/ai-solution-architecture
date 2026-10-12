"""Shadow deployment analysis (champion vs shadow on mirrored traffic).

``serving/k8s/virtualservice-mirror.yaml`` mirrors production requests to the
``<isvc>-shadow`` InferenceService. Its transformer runs in shadow mode
(``SHADOW_MODE=true``): for every mirrored request it scores the *same* feature
vector on both the shadow predictor and the champion predictor and exports

* ``churn_shadow_pairs_total{isvc, tier_agree="true|false"}`` (counter)
* ``churn_shadow_rank_corr{isvc}`` (gauge: Spearman over a rolling reservoir)

Checks, over ``--window``:

* paired requests                >= ``--min-pairs``
* mirror ratio (shadow/champion) >= ``--min-mirror-ratio`` (mirroring works)
* Spearman rank correlation      >= ``--min-rank-corr`` (min across pods)
* risk-tier agreement            >= ``--min-tier-agreement``
* shadow p99 latency             <= ``--max-p99-ms``
* shadow 5xx rate                <= ``--max-error-rate``

Two modes:

* ``--window 30m`` polls every ``--interval`` while traffic accumulates and
  fails fast on a breach (warm-up gate right after the shadow is deployed);
* ``--lookback 7d`` evaluates once over an already-elapsed period (the 7-day
  shadow soak in system-design.md 6.4 step 7; the ``shadow-analysis`` job runs
  after a GitHub environment wait timer, so nothing sleeps for 7 days).

Exit codes: 0 = pass, 1 = breach, 2 = inconclusive.
"""

from __future__ import annotations

import argparse
import json
import os
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
    observe,
    parse_duration,
    promql_duration,
    render,
)


def collect(
    prom: PrometheusClient, namespace: str, champion: str, shadow: str, window_s: int
) -> dict:
    w = promql_duration(window_s)

    def istio(isvc: str, extra: str = "") -> str:
        return (
            f'reporter="destination",destination_workload_namespace="{namespace}",'
            f'destination_workload=~"{isvc}-transformer-.*-deployment"{extra}'
        )

    champ_req = prom.scalar(f"sum(increase(istio_requests_total{{{istio(champion)}}}[{w}]))")
    shadow_req = prom.scalar(f"sum(increase(istio_requests_total{{{istio(shadow)}}}[{w}]))")
    shadow_5xx_sel = istio(shadow, ',response_code=~"5.."')
    shadow_5xx = prom.scalar(f"sum(increase(istio_requests_total{{{shadow_5xx_sel}}}[{w}]))")
    p99 = prom.scalar(
        "histogram_quantile(0.99, sum by (le) "
        f"(rate(istio_request_duration_milliseconds_bucket{{{istio(shadow)}}}[{w}])))"
    )
    pairs_sel = f'namespace="{namespace}",isvc="{shadow}"'
    pairs = prom.scalar(f"sum(increase(churn_shadow_pairs_total{{{pairs_sel}}}[{w}]))")
    agree = prom.scalar(
        f'sum(increase(churn_shadow_pairs_total{{{pairs_sel},tier_agree="true"}}[{w}]))'
    )
    rank_corr = prom.scalar(f"min(last_over_time(churn_shadow_rank_corr{{{pairs_sel}}}[{w}]))")
    return {
        "champion_requests": champ_req,
        "shadow_requests": shadow_req,
        "error_rate": None if not shadow_req else (shadow_5xx or 0.0) / shadow_req,
        "p99_ms": p99,
        "pairs": pairs,
        "tier_agreement": None if not pairs else (agree or 0.0) / pairs,
        "rank_corr": rank_corr,
    }


def evaluate(snap: dict, args: argparse.Namespace) -> tuple[int, list[dict]]:
    checks: list[dict] = []

    def at_least(name: str, actual: Any, limit: float) -> None:
        checks.append(
            {
                "check": name,
                "actual": actual,
                "limit": limit,
                "ok": None if actual is None else actual >= limit,
            }
        )

    def at_most(name: str, actual: Any, limit: float) -> None:
        checks.append(
            {
                "check": name,
                "actual": actual,
                "limit": limit,
                "ok": None if actual is None else actual <= limit,
            }
        )

    pairs = snap.get("pairs") or 0.0
    at_least("paired_requests", pairs, args.min_pairs)
    champ, shadow = snap.get("champion_requests"), snap.get("shadow_requests")
    at_least("mirror_ratio", None if not champ else (shadow or 0.0) / champ, args.min_mirror_ratio)
    at_least("rank_corr", snap.get("rank_corr"), args.min_rank_corr)
    at_least("tier_agreement", snap.get("tier_agreement"), args.min_tier_agreement)
    at_most("p99_ms", snap.get("p99_ms"), args.max_p99_ms)
    at_most("error_rate", snap.get("error_rate"), args.max_error_rate)

    enough = pairs >= args.min_pairs
    if enough and any(c["ok"] is False for c in checks):
        return EXIT_FAIL, checks
    if not enough or any(c["ok"] is None for c in checks):
        return EXIT_INCONCLUSIVE, checks
    return EXIT_PASS, checks


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m churn.deploy.shadow_analysis", description=__doc__)
    p.add_argument("--prometheus-url")
    p.add_argument("--namespace", default="churn-serving")
    p.add_argument("--champion", required=True, help="champion InferenceService name")
    p.add_argument("--shadow", required=True, help="shadow InferenceService name")
    p.add_argument("--window", default="2h")
    p.add_argument("--interval", default="5m")
    p.add_argument(
        "--lookback",
        help="evaluate once over this elapsed period (e.g. 7d) instead of polling --window",
    )
    p.add_argument("--min-rank-corr", type=float, required=True)
    p.add_argument("--min-tier-agreement", type=float, required=True)
    p.add_argument("--max-p99-ms", type=float, required=True)
    p.add_argument("--max-error-rate", type=float, required=True)
    p.add_argument("--min-pairs", type=float, default=1000)
    p.add_argument("--min-mirror-ratio", type=float, default=0.5)
    p.add_argument("--input-json", help="evaluate a pre-collected snapshot (offline)")
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
            return evaluate(json.load(fh), args)
    if not args.prometheus_url and prom is None:
        raise ValueError("--prometheus-url is required unless --input-json is given")
    prom = prom or PrometheusClient(args.prometheus_url)

    def step(lookback: int) -> tuple[int, list[dict]]:
        return evaluate(collect(prom, args.namespace, args.champion, args.shadow, lookback), args)

    if args.lookback:
        return step(parse_duration(args.lookback))
    return observe(parse_duration(args.window), parse_duration(args.interval), step, clock, sleep)


def main(argv: list[str] | None = None, **kwargs: Any) -> int:
    args = build_parser().parse_args(argv)
    try:
        code, checks = run(args, **kwargs)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: shadow analysis could not run: {exc}", file=sys.stderr)
        return EXIT_INCONCLUSIVE
    report = render(code, checks, f"Shadow analysis {args.champion} vs {args.shadow}")
    print(report)
    append_file(args.summary or os.environ.get("GITHUB_STEP_SUMMARY"), report)
    return code


if __name__ == "__main__":
    sys.exit(main())
