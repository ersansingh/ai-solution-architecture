"""Target-leakage and temporal-integrity checks (stdlib only).

Used by ``tests/leakage`` in CI against the Gold fixture and by the Azure ML
evaluate step (``max_single_feature_auc`` in the evaluation report).
"""

from __future__ import annotations

import fnmatch
from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date, datetime

# Signals that only exist after the customer has decided to leave.
FORBIDDEN_FEATURE_PATTERNS = (
    "*cancel*",
    "*port_out*",
    "*porting*",
    "*termination*",
    "*churn_date*",
    "*disconnect_request*",
    "*winback*",
)


def _to_date(value: str | date) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def point_in_time_violations(
    rows: Iterable[dict], feature_ts_col: str, snapshot_col: str
) -> list[dict]:
    """Rows whose feature timestamp is after the snapshot date (future leakage)."""
    return [r for r in rows if _to_date(r[feature_ts_col]) > _to_date(r[snapshot_col])]


def label_window_violations(
    rows: Iterable[dict], label_start_col: str, snapshot_col: str
) -> list[dict]:
    """Rows whose label window starts before the snapshot (label from pre-snapshot data)."""
    return [r for r in rows if _to_date(r[label_start_col]) < _to_date(r[snapshot_col])]


def forbidden_columns(
    columns: Iterable[str], patterns: Sequence[str] = FORBIDDEN_FEATURE_PATTERNS
) -> list[str]:
    """Feature columns that look like post-churn signals."""
    return sorted(c for c in columns if any(fnmatch.fnmatch(c.lower(), p) for p in patterns))


def split_overlap(rows: Iterable[dict], id_col: str, split_col: str) -> dict[str, set[str]]:
    """Customer ids that appear in more than one split -> {id: {splits}}."""
    seen: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        seen[r[id_col]].add(r[split_col])
    return {cid: s for cid, s in seen.items() if len(s) > 1}


def roc_auc(scores: Sequence[float], labels: Sequence[int]) -> float:
    """Rank-based (Mann-Whitney) ROC-AUC with tie handling."""
    if len(scores) != len(labels):
        raise ValueError("scores and labels differ in length")
    pos = sum(1 for y in labels if y == 1)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        raise ValueError("ROC-AUC needs both classes")
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    rank_sum_pos = sum(r for r, y in zip(ranks, labels) if y == 1)
    return (rank_sum_pos - pos * (pos + 1) / 2.0) / (pos * neg)


def single_feature_aucs(
    rows: Sequence[dict], feature_cols: Iterable[str], label_col: str
) -> dict[str, float]:
    """Direction-agnostic AUC (max(auc, 1-auc)) of each numeric feature alone."""
    labels = [int(float(r[label_col])) for r in rows]
    out: dict[str, float] = {}
    for col in feature_cols:
        try:
            values = [float(r[col]) for r in rows]
        except (TypeError, ValueError):
            continue
        auc = roc_auc(values, labels)
        out[col] = max(auc, 1.0 - auc)
    return out
