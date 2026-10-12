"""Post-promotion smoke test of the Churn Scoring API through internal APIM.

Calls ``GET {endpoint}/customers/{pseudoId}/score`` (``--endpoint`` is the API
base, e.g. ``https://apim-churn-prod.internal/churn/v1``) for ``--samples``
requests, cycling through synthetic smoke-test customers that are seeded in the
Feast online store (``--ids-file``). Every response must be HTTP 200 with a
valid body: ``probability`` in [0, 1], ``tier`` in {A, B, LOW, UNKNOWN},
at most 5 ``reason_codes``, and a ``model_version``.

Latency is checked on two clocks, because the 50 ms / 150 ms SLOs are
*service-side* (system-design.md 6.2) while this test runs through APIM:

* server-side: the transformer stamps every response with
  ``x-churn-server-time-ms`` (``--server-timing-header``; time spent inside the
  transformer pod incl. Feast lookup, predictor hop and TreeSHAP). p99 per path
  must be <= ``--max-server-p99-ms`` (precomputed, ``freshness != "fresh"``) and
  <= ``--max-server-rescore-p99-ms`` (rescoring, ``freshness == "fresh"``). A
  200 response without the header is an error (the SLO cannot be verified).
* client-side: end-to-end through APIM, the private network and the Istio
  ingress gateway. p99 must be <= ``--max-client-p99-ms``, a looser bound
  (default 300 ms, the p99 alert threshold in system-design.md 7; APIM's hop
  timeout is 400 ms).

Auth: ``CHURN_API_TOKEN`` if set, otherwise an Entra ID client-credentials
token for ``--scope`` (default ``$CHURN_API_SCOPE``) via ``azure-identity``.

Exit codes: 0 = pass, 1 = fail.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

VALID_TIERS = {"A", "B", "LOW", "UNKNOWN"}
DEFAULT_IDS_FILE = "tests/fixtures/smoke_customer_ids.txt"
# Set by serving/churn_serving/timing.py (ServerTimingMiddleware)
SERVER_TIMING_HEADER = "x-churn-server-time-ms"


def p99(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(math.ceil(0.99 * len(ordered)) - 1, 0)]


def validate_body(body: dict[str, Any]) -> str | None:
    """Return an error message, or None when the response body is valid."""
    prob = body.get("probability")
    if not isinstance(prob, (int, float)) or not 0.0 <= prob <= 1.0:
        return f"probability out of range: {prob!r}"
    if body.get("tier") not in VALID_TIERS:
        return f"invalid tier: {body.get('tier')!r}"
    codes = body.get("reason_codes")
    if not isinstance(codes, list) or len(codes) > 5:
        return f"invalid reason_codes: {codes!r}"
    if not body.get("model_version"):
        return "model_version missing"
    return None


def get_token(scope: str | None) -> str | None:
    token = os.environ.get("CHURN_API_TOKEN")
    if token or not scope:
        return token
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential().get_token(scope).token


def load_ids(path: str) -> list[str]:
    ids = [ln.strip() for ln in Path(path).read_text().splitlines()]
    ids = [i for i in ids if i and not i.startswith("#")]
    if not ids:
        raise ValueError(f"no customer ids in {path}")
    return ids


def server_time_ms(headers: Any, name: str) -> float | None:
    """Parse the transformer's server-timing header (milliseconds)."""
    raw = headers.get(name) if headers is not None else None
    if raw is None:
        return None
    try:
        value = float(str(raw).strip())
    except ValueError:
        return None
    return value if value >= 0 else None


def run(
    args: argparse.Namespace,
    opener: Callable[..., Any] = urllib.request.urlopen,
    clock: Callable[[], float] = time.perf_counter,
    token: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    if not args.endpoint.startswith("https://"):
        raise ValueError("--endpoint must be an https URL")
    ids = load_ids(args.ids_file)
    base = args.endpoint.rstrip("/")
    client_ms: list[float] = []
    server_ms: dict[str, list[float]] = {"precomputed": [], "rescore": []}
    errors: list[str] = []
    for i in range(args.samples):
        cid = urllib.parse.quote(ids[i % len(ids)], safe="")
        req = urllib.request.Request(f"{base}/customers/{cid}/score")
        req.add_header("Accept", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        start = clock()
        try:
            with opener(req, timeout=args.timeout) as resp:  # nosec B310
                status, raw = resp.status, resp.read()
                headers = getattr(resp, "headers", None)
            client_ms.append((clock() - start) * 1000.0)
            err = None
            if status != 200:
                err = f"HTTP {status}"
            else:
                body = json.loads(raw.decode())
                err = validate_body(body)
                served = server_time_ms(headers, args.server_timing_header)
                if served is None:
                    err = err or f"missing/invalid {args.server_timing_header} header"
                else:
                    path = "rescore" if body.get("freshness") == "fresh" else "precomputed"
                    server_ms[path].append(served)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            client_ms.append((clock() - start) * 1000.0)
            err = f"{type(exc).__name__}: {exc}"
        if err:
            errors.append(f"{ids[i % len(ids)]}: {err}")

    error_rate = len(errors) / args.samples
    client_p99 = p99(client_ms)
    pre_p99 = p99(server_ms["precomputed"]) if server_ms["precomputed"] else None
    res_p99 = p99(server_ms["rescore"]) if server_ms["rescore"] else None
    checks = {
        "error_rate": error_rate <= args.max_error_rate,
        "client_p99": client_p99 <= args.max_client_p99_ms,
        "server_p99_precomputed": pre_p99 is None or pre_p99 <= args.max_server_p99_ms,
        "server_p99_rescore": res_p99 is None or res_p99 <= args.max_server_rescore_p99_ms,
        "server_timing_observed": pre_p99 is not None or res_p99 is not None,
    }
    return all(checks.values()), {
        "samples": args.samples,
        "errors": len(errors),
        "error_rate": error_rate,
        "client_p99_ms": client_p99,
        "server_p99_ms": {"precomputed": pre_p99, "rescore": res_p99},
        "server_samples": {k: len(v) for k, v in server_ms.items()},
        "checks": checks,
        "first_errors": errors[:5],
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m churn.deploy.smoke_test", description=__doc__)
    p.add_argument("--endpoint", required=True, help="API base URL incl. /churn/v1")
    p.add_argument("--samples", type=int, default=200)
    p.add_argument(
        "--max-server-p99-ms",
        type=float,
        required=True,
        help="service-side p99 SLO, precomputed path (server-timing header)",
    )
    p.add_argument(
        "--max-server-rescore-p99-ms",
        type=float,
        default=150.0,
        help="service-side p99 SLO, rescoring path (server-timing header)",
    )
    p.add_argument(
        "--max-client-p99-ms",
        type=float,
        default=300.0,
        help="end-to-end p99 through APIM (looser than the service-side SLO)",
    )
    p.add_argument("--server-timing-header", default=SERVER_TIMING_HEADER)
    p.add_argument("--max-error-rate", type=float, default=0.0)
    p.add_argument("--ids-file", default=DEFAULT_IDS_FILE)
    p.add_argument("--scope", default=os.environ.get("CHURN_API_SCOPE"))
    p.add_argument("--timeout", type=float, default=2.0)
    return p


def main(argv: list[str] | None = None, **kwargs: Any) -> int:
    args = build_parser().parse_args(argv)
    if args.samples <= 0:
        print("ERROR: --samples must be positive", file=sys.stderr)
        return 1
    try:
        kwargs.setdefault("token", get_token(args.scope))
        ok, result = run(args, **kwargs)
    except (ValueError, OSError) as exc:
        print(f"ERROR: smoke test could not run: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    print("SMOKE TEST " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
