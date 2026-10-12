"""Out-of-time evaluation -> ``evaluation_report`` (consumed by churn.evaluation.gates).

Writes to ``--evaluation-report``:

* ``metrics.json``         candidate / champion / LR baseline / fairness / latency / leakage
* ``model_card.md``        intended use, data window, metrics by tier and segment, limitations
* ``fairness_report.html`` per-group selection rate, TPR and FPR

``gates.json`` is added later by the GitHub ``ct-evaluate`` job.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import lightgbm as lgb
import mlflow
import numpy as np
import pandas as pd
from common import (
    FAIRNESS_ATTRIBUTES,
    LABEL_COL,
    apply_isotonic,
    expected_calibration_error,
    read_split,
    tier_metrics,
    top_decile,
    write_json,
)
from mlflow import MlflowClient
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def score_package(folder: Path, df: pd.DataFrame) -> tuple[np.ndarray, dict]:
    cfg = json.loads((folder / "calibrator.json").read_text())
    booster = lgb.Booster(model_file=str(folder / "model.bst"))
    return apply_isotonic(booster.predict(df[cfg["features"]]), cfg), cfg


def core_metrics(y: np.ndarray, p: np.ndarray, cfg: dict) -> dict:
    lift, recall_td = top_decile(y, p)
    tier_a_precision, tier_b_recall = tier_metrics(y, p, cfg)
    return {
        "pr_auc": float(average_precision_score(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "ece": expected_calibration_error(y, p),
        "lift_top_decile": lift,
        "recall_top_decile": recall_td,
        "tier_a_precision": tier_a_precision,
        "tier_b_recall": tier_b_recall,
        "accuracy_info_only": float(((p >= 0.5) == y).mean()),
    }


def champion_metrics(model_name: str, alias: str, test: pd.DataFrame) -> dict | None:
    """Score the current champion on the same OOT test set (None on first release)."""
    try:
        mv = MlflowClient().get_model_version_by_alias(model_name, alias)
    except Exception as exc:  # noqa: BLE001 - no champion yet
        print(f"no champion '{alias}' for {model_name}: {exc}")
        return None
    local = Path(mlflow.artifacts.download_artifacts(f"models:/{model_name}@{alias}"))
    try:
        p, cfg = score_package(local, test)
    except (FileNotFoundError, KeyError) as exc:
        print(f"champion v{mv.version} not scorable on this feature set: {exc}")
        return None
    y = test[LABEL_COL].astype(int).to_numpy()
    return {"model_version": mv.version, **core_metrics(y, p, cfg)}


def lr_baseline(train, test, features, y, p, n_boot=200, seed=11) -> dict:
    """Logistic-regression baseline + bootstrap 95% CI of the ROC-AUC gain."""
    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced"))
    lr.fit(train[features].fillna(0), train[LABEL_COL].astype(int))
    p_lr = lr.predict_proba(test[features].fillna(0))[:, 1]
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            continue
        deltas.append(roc_auc_score(y[idx], p[idx]) - roc_auc_score(y[idx], p_lr[idx]))
    return {
        "roc_auc": float(roc_auc_score(y, p_lr)),
        "pr_auc": float(average_precision_score(y, p_lr)),
        "roc_auc_delta_ci_low": float(np.percentile(deltas, 2.5)),
        "roc_auc_delta_ci_high": float(np.percentile(deltas, 97.5)),
    }


def fairness(test: pd.DataFrame, y: np.ndarray, p: np.ndarray, threshold: float) -> dict:
    flagged = p >= threshold
    out = {}
    for attr in FAIRNESS_ATTRIBUTES:
        if attr not in test.columns:
            continue
        groups = {}
        for g, idx in test.groupby(attr).indices.items():
            yy, ff = y[idx], flagged[idx]
            groups[str(g)] = {
                "n": int(len(idx)),
                "selection_rate": float(ff.mean()),
                "tpr": float(ff[yy == 1].mean()) if (yy == 1).any() else float("nan"),
                "fpr": float(ff[yy == 0].mean()) if (yy == 0).any() else float("nan"),
            }
        sel = [v["selection_rate"] for v in groups.values()]
        tpr = [v["tpr"] for v in groups.values() if not np.isnan(v["tpr"])]
        fpr = [v["fpr"] for v in groups.values() if not np.isnan(v["fpr"])]
        out[attr] = {
            "disparate_impact": float(min(sel) / max(sel)) if max(sel) > 0 else 1.0,
            "equal_opportunity_diff": float(max(tpr) - min(tpr)) if tpr else None,
            "fpr_diff": float(max(fpr) - min(fpr)) if fpr else None,
            "groups": groups,
        }
    return out


def latency_benchmark(booster: lgb.Booster, cfg: dict, x: np.ndarray, n: int = 2000) -> dict:
    """In-process single-row timings on the evaluation node (container-equivalent)."""
    rescore, precomputed = [], []
    record = {"probability": 0.1, "tier": "LOW", "reason_codes": [], "model_version": "x"}
    for i in range(n):
        row = x[i % len(x)][None, :]
        t0 = time.perf_counter()
        apply_isotonic(booster.predict(row), cfg)
        booster.predict(row, pred_contrib=True)
        rescore.append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        json.dumps(record)
        precomputed.append((time.perf_counter() - t0) * 1000)
    return {
        "p99_rescore_ms": float(np.percentile(rescore, 99)),
        "p99_precomputed_ms": float(np.percentile(precomputed, 99)),
        "samples": n,
    }


def shap_share(booster: lgb.Booster, x: np.ndarray, features: list[str]) -> tuple[float, dict]:
    contrib = np.abs(booster.predict(x, pred_contrib=True)[:, :-1]).mean(axis=0)
    share = contrib / contrib.sum()
    importance = dict(sorted(zip(features, share.tolist()), key=lambda kv: -kv[1]))
    return float(share.max()), importance


def model_card(metrics: dict, info: dict, data_window: dict) -> str:
    c, champ = metrics["candidate"], metrics.get("champion") or {}
    rows = "\n".join(
        f"| {k} | {c.get(k, float('nan')):.4f} | {champ.get(k, float('nan')) if champ else 'n/a'} |"
        for k in (
            "pr_auc",
            "roc_auc",
            "lift_top_decile",
            "tier_a_precision",
            "tier_b_recall",
            "brier",
            "ece",
        )
    )
    fair = "\n".join(
        f"| {a} | {v['disparate_impact']:.3f} | {v['equal_opportunity_diff']} | {v['fpr_diff']} |"
        for a, v in metrics["fairness"].items()
    )
    top = ", ".join(list(metrics["global_importance"])[:10])
    return f"""# Model card: churn-lightgbm candidate (run {c["run_id"]})

**Intended use**: rank active customers by 90-day churn risk for tiered retention actions
(Tier A costly offers, Tier B low-cost nudges). Decision support with HITL review.
**Out of scope**: credit, pricing or any automated adverse decision; non-EU customers.

**Training data window**: {data_window}
**Algorithm**: LightGBM + isotonic calibration (CatBoost challenger validation PR-AUC
{info["catboost_valid_pr_auc"]:.4f} vs LightGBM {info["lightgbm_valid_pr_auc"]:.4f};
challenger_wins={info["challenger_wins"]}).

## Out-of-time metrics

| Metric | Candidate | Champion |
|---|---|---|
{rows}

Accuracy is reported for information only: {c["accuracy_info_only"]:.4f}.

## Fairness (Tier B operating point)

| Attribute | Disparate impact | Equal-opportunity diff | FPR diff |
|---|---|---|---|
{fair}

## Explanation method
TreeSHAP (LightGBM pred_contrib). Top global drivers: {top}.

## Known limitations
Labels mature 90 days after the snapshot; latency figures are in-process benchmarks,
end-to-end SLOs are verified in shadow and canary. Approvers: DS lead, Model Risk Owner (+DPO).
"""


def fairness_html(fair: dict) -> str:
    rows = "".join(
        f"<tr><td>{a}</td><td>{g}</td><td>{v['n']}</td><td>{v['selection_rate']:.3f}</td>"
        f"<td>{v['tpr']:.3f}</td><td>{v['fpr']:.3f}</td></tr>"
        for a, d in fair.items()
        for g, v in d["groups"].items()
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Churn fairness report</title>"
        "</head><body><h1>Fairness report (Tier B threshold)</h1><table border='1'>"
        "<tr><th>Attribute</th><th>Group</th><th>n</th><th>Selection rate</th><th>TPR</th>"
        f"<th>FPR</th></tr>{rows}</table></body></html>"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-model", required=True)
    ap.add_argument("--train-data", required=True)
    ap.add_argument("--test-data", required=True)
    ap.add_argument("--model-name", default="churn-lightgbm")
    ap.add_argument("--champion-alias", default="champion")
    ap.add_argument("--evaluation-report", required=True)
    args = ap.parse_args()

    cand_dir, report = Path(args.candidate_model), Path(args.evaluation_report)
    info = json.loads((cand_dir / "candidate_info.json").read_text())
    train, test = read_split(args.train_data), read_split(args.test_data)
    y = test[LABEL_COL].astype(int).to_numpy()
    p, cfg = score_package(cand_dir, test)
    features = cfg["features"]
    booster = lgb.Booster(model_file=str(cand_dir / "model.bst"))
    x = test[features].to_numpy(dtype=np.float32)

    max_share, importance = shap_share(booster, x[:20000], features)
    single_auc = {
        f: max(a, 1 - a)
        for f in features
        if test[f].nunique() > 1
        for a in [roc_auc_score(y, test[f].fillna(test[f].median()))]
    }
    metrics = {
        "candidate": {
            "run_id": info["run_id"],
            "algorithm": info["algorithm"],
            **core_metrics(y, p, cfg),
            "shap_max_share": max_share,
        },
        "champion": champion_metrics(args.model_name, args.champion_alias, test),
        "baseline": lr_baseline(train, test, features, y, p),
        "fairness": fairness(test, y, p, cfg["tier_b_threshold"]),
        "latency": latency_benchmark(booster, cfg, x),
        "leakage": {
            "max_single_feature_auc": max(single_auc.values()),
            "top_single_feature_aucs": dict(sorted(single_auc.items(), key=lambda kv: -kv[1])[:5]),
        },
        "global_importance": importance,
        "data": {"test_rows": int(len(test)), "test_positive_rate": float(y.mean())},
    }
    window = {
        "train_from": str(train["snapshot_date"].min()),
        "train_to": str(train["snapshot_date"].max()),
        "test_snapshot": str(test["snapshot_date"].max()),
    }
    write_json(metrics, report / "metrics.json")
    (report / "model_card.md").write_text(model_card(metrics, info, window))
    (report / "fairness_report.html").write_text(fairness_html(metrics["fairness"]))
    with mlflow.start_run():
        mlflow.log_metrics(
            {f"oot_{k}": v for k, v in metrics["candidate"].items() if isinstance(v, float)}
        )
        mlflow.log_artifacts(str(report), artifact_path="evaluation_report")


if __name__ == "__main__":
    main()
