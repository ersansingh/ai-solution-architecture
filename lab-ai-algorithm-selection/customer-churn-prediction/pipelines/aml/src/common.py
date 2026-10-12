"""Shared helpers for the churn Azure ML pipeline components."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ID_COL = "pseudo_customer_id"
TIME_COL = "event_timestamp"
LABEL_COL = "churn_90d"
# Audit-only and bookkeeping columns: never model features (system-design.md 7.6)
NON_FEATURES = {
    ID_COL,
    TIME_COL,
    LABEL_COL,
    "snapshot_date",
    "split",
    "country",
    "region",
    "age_band",
    "gender",
    "label_window_start",
    "feature_event_ts",
}
FAIRNESS_ATTRIBUTES = ("age_band", "gender", "region")


def read_split(folder: str) -> pd.DataFrame:
    return pd.read_parquet(Path(folder) / "data.parquet")


def write_split(df: pd.DataFrame, folder: str) -> None:
    Path(folder).mkdir(parents=True, exist_ok=True)
    df.to_parquet(Path(folder) / "data.parquet", index=False)


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_FEATURES and pd.api.types.is_numeric_dtype(df[c])]


def write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=float))


def apply_isotonic(raw: np.ndarray, cfg: dict) -> np.ndarray:
    xs, ys = cfg["calibrator"]["x"], cfg["calibrator"]["y"]
    return np.interp(raw, xs, ys)


def expected_calibration_error(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    ece = 0.0
    for b in range(bins):
        mask = idx == b
        if mask.any():
            ece += mask.mean() * abs(y[mask].mean() - p[mask].mean())
    return float(ece)


def top_decile(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    """(lift@top-decile, recall@top-decile)."""
    k = max(int(len(p) * 0.1), 1)
    top = np.argsort(-p)[:k]
    base = y.mean()
    return float(y[top].mean() / base) if base else 0.0, float(y[top].sum() / max(y.sum(), 1))


def tier_metrics(y: np.ndarray, p: np.ndarray, cfg: dict) -> tuple[float, float]:
    """(Tier A precision, Tier B recall) at the calibrated thresholds."""
    a = p >= cfg["tier_a_threshold"]
    b = p >= cfg["tier_b_threshold"]
    precision_a = float(y[a].mean()) if a.any() else 0.0
    recall_b = float(y[b].sum() / max(y.sum(), 1))
    return precision_a, recall_b


# Business-readable reason codes for TreeSHAP drivers (unknown -> FEATURE_NAME)
REASON_CODES = {
    "monthly_charges": "BILL_SHOCK",
    "bill_change_3m_pct": "BILL_SHOCK",
    "data_usage_30d_delta_pct": "USAGE_DECLINE_30D",
    "app_sessions_30d": "LOW_DIGITAL_ENGAGEMENT",
    "support_tickets_90d": "REPEAT_COMPLAINT",
    "tickets_24h": "RECENT_COMPLAINT",
    "failed_payments_90d": "PAYMENT_FRICTION",
    "failed_payments_7d": "PAYMENT_FRICTION",
    "contract_months_remaining": "CONTRACT_ENDING",
    "tenure_months": "SHORT_TENURE",
    "dropped_calls_30d": "SERVICE_QUALITY",
}
