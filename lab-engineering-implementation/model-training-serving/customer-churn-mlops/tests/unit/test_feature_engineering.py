import numpy as np
import pandas as pd

from churn.feature_engineering import add_engineered_features


def _row(**overrides):
    base = dict(age=30, tenure_months=0, monthly_charges=50.0, total_charges=0.0, outstanding_balance=10.0,
                avg_days_past_due=15.0, voice_minutes=1500, data_usage_gb=110.0, data_usage_gb_prev_3m=100.0,
                support_calls=4, tickets=0, complaint_count=2, satisfaction_score=7)
    base.update(overrides)
    return pd.DataFrame([base])


def test_formulas_on_raw_values():
    out = add_engineered_features(_row(tenure_months=9, total_charges=500.0)).iloc[0]
    assert out["average_monthly_spend"] == 50.0
    assert out["customer_lifetime_value"] == 450.0
    assert out["support_frequency"] == 0.4
    assert np.isclose(out["usage_growth_rate"], 10 / 101)
    assert out["complaint_ratio"] == 2.0
    assert np.isclose(out["payment_delay_score"], 0.5 + 10 / 51)
    assert out["customer_risk_score"] == 2 * 2 + 4 + 3
    assert out["age_band"] == "25-34"


def test_zero_denominators_do_not_produce_inf():
    out = add_engineered_features(_row(tenure_months=0, tickets=0, data_usage_gb_prev_3m=0.0))
    assert np.isfinite(out.select_dtypes("number").to_numpy()).all()


def test_engagement_score_is_population_independent():
    single = add_engineered_features(_row())["engagement_score"].iloc[0]
    many = add_engineered_features(pd.concat([_row(), _row(voice_minutes=10, data_usage_gb=1.0)]))
    assert many["engagement_score"].iloc[0] == single


def test_missing_age_keeps_missing_band():
    out = add_engineered_features(_row(age=np.nan))
    assert pd.isna(out["age_band"].iloc[0])
