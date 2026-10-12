"""Target-leakage and temporal-integrity tests on the Gold training fixture.

- no feature timestamp > snapshot_date (point-in-time joins)
- churn label only from the post-snapshot window
- no post-churn signals (cancellation tickets, port-out requests)
- single-feature AUC < 0.95 sanity check
- train/valid/calib/test splits have no customer overlap
- split dates are strictly ordered (out-of-time validation)
"""

import csv
from pathlib import Path

import pytest

from churn import leakage

GOLD = Path(__file__).resolve().parents[1] / "fixtures/contract_samples/gold_customer_features.csv"
NON_FEATURES = {
    "pseudo_customer_id",
    "country",
    "region",
    "age_band",
    "snapshot_date",
    "feature_event_ts",
    "label_window_start",
    "split",
    "churn_90d",
}
SPLIT_ORDER = ["train", "valid", "calib", "test"]


@pytest.fixture(scope="module")
def rows():
    with GOLD.open(newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def features(rows):
    return [c for c in rows[0] if c not in NON_FEATURES]


def test_no_future_feature_timestamps(rows):
    assert leakage.point_in_time_violations(rows, "feature_event_ts", "snapshot_date") == []


def test_label_from_post_snapshot_window(rows):
    assert leakage.label_window_violations(rows, "label_window_start", "snapshot_date") == []


def test_no_post_churn_signals(features):
    assert leakage.forbidden_columns(features) == []


def test_fairness_attributes_not_model_features(features):
    assert not {"age_band", "region", "gender"} & set(features)


def test_single_feature_auc_below_threshold(rows, features):
    aucs = leakage.single_feature_aucs(rows, features, "churn_90d")
    assert aucs, "no numeric features found"
    suspicious = {k: round(v, 3) for k, v in aucs.items() if v >= 0.95}
    assert suspicious == {}


def test_no_customer_overlap_between_splits(rows):
    assert leakage.split_overlap(rows, "pseudo_customer_id", "split") == {}


def test_out_of_time_split_ordering(rows):
    by_split = {}
    for r in rows:
        by_split.setdefault(r["split"], []).append(r["snapshot_date"])
    present = [s for s in SPLIT_ORDER if s in by_split]
    for earlier, later in zip(present, present[1:]):
        assert max(by_split[earlier]) < min(by_split[later]), (earlier, later)
