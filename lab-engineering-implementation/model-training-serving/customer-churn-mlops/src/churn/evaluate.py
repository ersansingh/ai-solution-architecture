"""Metrics, threshold selection and the evaluation.json contract (plan M5, section 6.5)."""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def select_threshold(y_true: np.ndarray, y_prob: np.ndarray, target_recall: float) -> float:
    """Highest-precision threshold whose recall is still >= target_recall (ADR-4)."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    # precision/recall have len(thresholds)+1 entries; the last point has no threshold.
    precision, recall = precision[:-1], recall[:-1]
    eligible = np.where(recall >= target_recall)[0]
    if len(eligible) == 0:
        return 0.5
    best = eligible[np.argmax(precision[eligible])]
    return float(thresholds[best])


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> Dict:
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    pr_p, pr_r, _ = precision_recall_curve(y_true, y_prob)
    step = max(1, len(fpr) // 200)
    pr_step = max(1, len(pr_p) // 200)

    def metric(value, std=None):
        return {"value": float(value), "standard_deviation": std if std is not None else "NaN"}

    # SageMaker Model Registry "model quality" layout + extra keys used by the pipeline.
    return {
        "binary_classification_metrics": {
            "accuracy": metric(accuracy_score(y_true, y_pred)),
            "precision": metric(precision_score(y_true, y_pred, zero_division=0)),
            "recall": metric(recall_score(y_true, y_pred, zero_division=0)),
            "f1": metric(f1_score(y_true, y_pred, zero_division=0)),
            "auc": metric(roc_auc_score(y_true, y_prob)),
            "pr_auc": metric(average_precision_score(y_true, y_prob)),
            "confusion_matrix": {"0": {"0": int(tn), "1": int(fp)}, "1": {"0": int(fn), "1": int(tp)}},
            "receiver_operating_characteristic_curve": {
                "false_positive_rates": fpr[::step].round(4).tolist(),
                "true_positive_rates": tpr[::step].round(4).tolist(),
            },
            "precision_recall_curve": {
                "precisions": pr_p[::pr_step].round(4).tolist(),
                "recalls": pr_r[::pr_step].round(4).tolist(),
            },
        },
        "threshold": float(threshold),
        "support": {"rows": int(len(y_true)), "positives": int(np.sum(y_true))},
    }


def gate_report(metrics: Dict, gates: Dict, approved_auc: Optional[float]) -> Dict:
    m = metrics["binary_classification_metrics"]
    auc = m["auc"]["value"]
    report = {
        "auc_ok": int(auc >= gates["auc"]),
        "precision_ok": int(m["precision"]["value"] >= gates["precision"]),
        "recall_ok": int(m["recall"]["value"] >= gates["recall"]),
        "accuracy_ok": int(m["accuracy"]["value"] >= gates["accuracy"]),
        "approved_auc": approved_auc,
        "no_regression_ok": int(approved_auc is None or auc >= approved_auc - gates["max_auc_regression"]),
    }
    report["all_blocking_ok"] = int(
        report["auc_ok"] and report["precision_ok"] and report["recall_ok"] and report["no_regression_ok"]
    )
    return report
