"""Business features (plan section 6.1). Pure functions over raw source columns."""
from __future__ import annotations

import numpy as np
import pandas as pd

AGE_BINS = [-np.inf, 24, 34, 49, 64, np.inf]
AGE_LABELS = ["<25", "25-34", "35-49", "50-64", "65+"]


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator / denominator
    return result.replace([np.inf, -np.inf], np.nan)


# Fixed reference ranges keep engagement_score identical for one record or a whole population.
ENGAGEMENT_SCALE = {"voice_minutes": 3000.0, "data_usage_gb": 1000.0, "complaint_count": 5.0}


def _scaled(series: pd.Series, column: str) -> pd.Series:
    return (series / ENGAGEMENT_SCALE[column]).clip(0, 1)


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with the 9 engineered features. Inputs must be on their raw scale."""
    out = df.copy()
    tenure_plus_one = out["tenure_months"] + 1

    out["average_monthly_spend"] = _safe_div(out["total_charges"], tenure_plus_one)
    out["customer_lifetime_value"] = out["monthly_charges"] * out["tenure_months"]
    out["support_frequency"] = _safe_div(out["support_calls"], tenure_plus_one)
    out["usage_growth_rate"] = _safe_div(
        out["data_usage_gb"] - out["data_usage_gb_prev_3m"], out["data_usage_gb_prev_3m"] + 1
    )
    out["complaint_ratio"] = _safe_div(out["complaint_count"], out["tickets"] + 1)
    out["payment_delay_score"] = out["avg_days_past_due"] / 30 + _safe_div(
        out["outstanding_balance"], out["monthly_charges"] + 1
    )
    out["customer_risk_score"] = (
        2 * out["complaint_count"] + out["support_calls"] + (10 - out["satisfaction_score"])
    )
    # Phase 3 engagement score, with inputs normalised first so GB and minutes are comparable.
    out["engagement_score"] = (
        _scaled(out["voice_minutes"], "voice_minutes")
        + _scaled(out["data_usage_gb"], "data_usage_gb")
        - _scaled(out["complaint_count"], "complaint_count")
    )
    out["age_band"] = pd.cut(out["age"], bins=AGE_BINS, labels=AGE_LABELS).astype(object)
    out.loc[out["age"].isna(), "age_band"] = np.nan
    return out
