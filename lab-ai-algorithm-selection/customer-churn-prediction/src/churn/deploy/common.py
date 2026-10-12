"""Shared helpers for shadow/canary analysis: Prometheus client, PSI, durations.

Prometheus is the Azure Monitor managed Prometheus workspace query endpoint
(``vars.AMW_PROMETHEUS_QUERY_URL``). It requires an Entra ID bearer token for
audience ``https://prometheus.monitor.azure.com``; the token is taken from
``PROMETHEUS_TOKEN`` or acquired with ``azure-identity`` (installed from
``serving/requirements-deploy.txt``; uses the runner's ``az login`` session).
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from typing import Any

PROMETHEUS_AUDIENCE = "https://prometheus.monitor.azure.com/.default"
_DURATION = re.compile(r"^(\d+)([smhd])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

# Exit codes shared by the analysis CLIs
EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_INCONCLUSIVE = 2


def parse_duration(value: str) -> int:
    """'30m' -> 1800 seconds."""
    m = _DURATION.match(value.strip())
    if not m:
        raise ValueError(f"invalid duration {value!r}; expected e.g. 90s, 30m, 2h")
    return int(m.group(1)) * _UNIT_SECONDS[m.group(2)]


def promql_duration(seconds: int) -> str:
    return f"{max(int(seconds), 60)}s"


def psi(expected: Sequence[float], actual: Sequence[float], eps: float = 1e-4) -> float:
    """Population stability index between two binned count/probability vectors."""
    if len(expected) != len(actual) or not expected:
        raise ValueError("PSI needs two non-empty vectors of equal length")
    e_total, a_total = float(sum(expected)), float(sum(actual))
    if e_total <= 0 or a_total <= 0:
        raise ValueError("PSI needs non-zero totals")
    value = 0.0
    for e, a in zip(expected, actual):
        pe = max(e / e_total, eps)
        pa = max(a / a_total, eps)
        value += (pa - pe) * math.log(pa / pe)
    return value


def cumulative_to_bins(buckets: dict[float, float]) -> list[float]:
    """Prometheus cumulative histogram {le: count} -> per-bin counts (sorted by le)."""
    out: list[float] = []
    prev = 0.0
    for le in sorted(buckets):
        out.append(max(buckets[le] - prev, 0.0))
        prev = buckets[le]
    return out


def bearer_token() -> str | None:
    token = os.environ.get("PROMETHEUS_TOKEN")
    if token:
        return token
    try:
        from azure.identity import DefaultAzureCredential
    except ImportError:
        return None
    return DefaultAzureCredential().get_token(PROMETHEUS_AUDIENCE).token


class PrometheusClient:
    """Minimal instant-query client for the Prometheus HTTP API."""

    def __init__(
        self,
        base_url: str,
        token_provider: Callable[[], str | None] = bearer_token,
        opener: Callable[..., Any] = urllib.request.urlopen,
        timeout: float = 30.0,
    ) -> None:
        if not base_url.startswith(("https://", "http://")):
            raise ValueError("prometheus URL must be http(s)")
        self.base_url = base_url.rstrip("/")
        self._token_provider = token_provider
        self._opener = opener
        self._timeout = timeout

    def query(self, promql: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/api/v1/query?" + urllib.parse.urlencode({"query": promql})
        req = urllib.request.Request(url)
        token = self._token_provider()
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with self._opener(req, timeout=self._timeout) as resp:  # nosec B310
            body = json.loads(resp.read().decode())
        if body.get("status") != "success":
            raise RuntimeError(f"prometheus query failed: {body.get('error', body)}")
        return body["data"]["result"]

    def scalar(self, promql: str) -> float | None:
        result = self.query(promql)
        if not result:
            return None
        value = float(result[0]["value"][1])
        return None if math.isnan(value) else value

    def histogram(self, promql: str) -> dict[float, float]:
        """Query returning one series per ``le`` label -> {le: value}."""
        out: dict[float, float] = {}
        for series in self.query(promql):
            le = series["metric"].get("le")
            if le is None:
                continue
            out[float("inf") if le == "+Inf" else float(le)] = float(series["value"][1])
        return out


def append_file(path: str | None, text: str) -> None:
    if path:
        with open(path, "a") as fh:
            fh.write(text)


def render(code: int, checks: list[dict], title: str) -> str:
    """Markdown table of analysis checks."""
    verdict = {EXIT_PASS: "PROMOTE", EXIT_FAIL: "ROLLBACK", EXIT_INCONCLUSIVE: "INCONCLUSIVE"}
    lines = [
        f"### {title}: {verdict[code]}",
        "",
        "| Check | Actual | Limit | OK |",
        "|---|---|---|---|",
    ]
    for c in checks:
        ok = {True: "yes", False: "NO", None: "n/a"}[c["ok"]]
        actual = "n/a" if c["actual"] is None else f"{c['actual']:.4g}"
        limit = "n/a" if c["limit"] is None else f"{c['limit']:.4g}"
        lines.append(f"| {c['check']} | {actual} | {limit} | {ok} |")
    return "\n".join(lines) + "\n"


def observe(
    window_s: int,
    interval_s: int,
    step: Callable[[int], tuple[int, list[dict]]],
    clock: Callable[[], float],
    sleep: Callable[[float], None],
) -> tuple[int, list[dict]]:
    """Poll ``step(lookback_seconds)`` every interval until the window ends.

    Returns early on EXIT_FAIL (fail fast); otherwise returns the verdict of
    the final poll at the end of the window.
    """
    start = clock()
    while True:
        sleep(min(interval_s, max(window_s - (clock() - start), 0)))
        elapsed = clock() - start
        code, checks = step(max(int(elapsed), 60))
        print(f"[{int(elapsed)}s] " + render(code, checks, "interim").splitlines()[0])
        if code == EXIT_FAIL or elapsed >= window_s:
            return code, checks
