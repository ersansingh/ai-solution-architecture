import json

import pandas as pd

from churn.data.generate_synthetic import generate
from churn.io import load_raw


def test_generated_layout_rate_nulls_and_duplicates(tmp_path):
    paths = generate(30_000, str(tmp_path), "2026-10-01", seed=3)
    manifest = json.loads(open(paths["manifest"]).read())
    assert abs(manifest["churn_rate"] - 0.18) < 0.015
    frames = load_raw(str(tmp_path / "raw-data"))
    assert set(frames) == {"customers", "billing", "usage", "support", "churn"}
    billing = frames["billing"]
    assert 0.02 < billing["monthly_charges"].isna().mean() < 0.06
    assert billing["customer_id"].duplicated().sum() > 0
    assert {"avg_days_past_due"} <= set(billing.columns)
    assert {"data_usage_gb_prev_3m"} <= set(frames["usage"].columns)


def test_scoring_population_has_no_labels(tmp_path):
    paths = generate(1_000, str(tmp_path), "2026-10-02", scoring=True, first_id=9_000_000)
    assert "churn" not in paths
    customers = pd.read_csv(paths["customers"])
    assert customers["customer_id"].min() == 9_000_000
