import numpy as np

from churn.evaluate import compute_metrics, gate_report, select_threshold

GATES = {"auc": 0.9, "precision": 0.85, "recall": 0.8, "accuracy": 0.9, "max_auc_regression": 0.01}


def _scores(seed=0, n=5000):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.18).astype(int)
    p = np.clip(y * 0.7 + rng.normal(0.15, 0.15, n), 0, 1)
    return y, p


def test_threshold_meets_target_recall():
    y, p = _scores()
    threshold = select_threshold(y, p, 0.82)
    recall = ((p >= threshold) & (y == 1)).sum() / y.sum()
    assert recall >= 0.82


def test_metrics_layout_matches_model_registry_format():
    y, p = _scores()
    m = compute_metrics(y, p, 0.5)
    bcm = m["binary_classification_metrics"]
    for key in ("accuracy", "precision", "recall", "f1", "auc", "pr_auc"):
        assert 0 <= bcm[key]["value"] <= 1
    cm = bcm["confusion_matrix"]
    assert sum(cm["0"].values()) + sum(cm["1"].values()) == len(y)


def test_gates_block_on_regression_against_approved_model():
    y, p = _scores()
    m = compute_metrics(y, p, select_threshold(y, p, 0.82))
    auc = m["binary_classification_metrics"]["auc"]["value"]
    assert gate_report(m, GATES, approved_auc=None)["no_regression_ok"] == 1
    report = gate_report(m, GATES, approved_auc=auc + 0.05)
    assert report["no_regression_ok"] == 0 and report["all_blocking_ok"] == 0
