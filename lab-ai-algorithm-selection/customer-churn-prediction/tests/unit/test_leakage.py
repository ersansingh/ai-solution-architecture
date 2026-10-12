import pytest

from churn import leakage


def test_point_in_time_and_label_window():
    rows = [
        {"snap": "2026-01-31", "fts": "2026-01-31T23:00:00Z", "lbl": "2026-02-01"},
        {"snap": "2026-01-31", "fts": "2026-02-02", "lbl": "2026-01-15"},
    ]
    assert leakage.point_in_time_violations(rows, "fts", "snap") == [rows[1]]
    assert leakage.label_window_violations(rows, "lbl", "snap") == [rows[1]]


def test_to_date_accepts_date_objects():
    from datetime import date, datetime

    assert leakage._to_date(datetime(2026, 1, 2, 3)) == date(2026, 1, 2)
    assert leakage._to_date(date(2026, 1, 2)) == date(2026, 1, 2)


def test_forbidden_columns():
    cols = ["tenure_months", "Cancellation_Ticket_Flag", "port_out_requested", "tickets_90d"]
    assert leakage.forbidden_columns(cols) == ["Cancellation_Ticket_Flag", "port_out_requested"]


def test_split_overlap():
    rows = [{"id": "a", "s": "train"}, {"id": "a", "s": "test"}, {"id": "b", "s": "train"}]
    assert leakage.split_overlap(rows, "id", "s") == {"a": {"train", "test"}}


def test_roc_auc_values():
    assert leakage.roc_auc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) == 1.0
    assert leakage.roc_auc([0.5, 0.5, 0.5, 0.5], [0, 1, 0, 1]) == 0.5
    assert leakage.roc_auc([0.9, 0.1], [0, 1]) == 0.0
    with pytest.raises(ValueError):
        leakage.roc_auc([0.1], [1])
    with pytest.raises(ValueError):
        leakage.roc_auc([0.1, 0.2], [1])


def test_single_feature_aucs_skips_non_numeric():
    rows = [{"x": "1", "c": "a", "y": "0"}, {"x": "2", "c": "b", "y": "1"}]
    assert leakage.single_feature_aucs(rows, ["x", "c"], "y") == {"x": 1.0}
