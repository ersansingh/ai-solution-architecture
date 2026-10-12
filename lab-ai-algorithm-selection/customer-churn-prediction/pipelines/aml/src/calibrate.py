"""Isotonic calibration on the out-of-time calibration fold + tier thresholds.

Produces the candidate model package (``--candidate-model``) that serving and
batch scoring consume, and logs it to MLflow under artifact path ``model`` in
this step's run (the run id is what the GitHub ``register-model`` job
registers):

* ``model.bst``        LightGBM booster (KServe MLServer LightGBM runtime)
* ``calibrator.json``  isotonic x/y knots, tier thresholds, feature list,
                       Feast feature refs and reason-code map (transformer)
* ``candidate_info.json`` run id + champion-candidate vs challenger benchmark

LightGBM is the served algorithm (``churn-lgbm`` InferenceService). CatBoost is
benchmarked every retrain; if it wins on validation PR-AUC this is recorded for
the Model Risk review rather than silently switching the serving runtime.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import lightgbm as lgb
import mlflow
import numpy as np
from common import LABEL_COL, REASON_CODES, read_split, write_json
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import precision_recall_curve


def tier_thresholds(y: np.ndarray, p: np.ndarray, capacity: float, recall_b: float) -> dict:
    order = np.sort(p)[::-1]
    k = max(int(len(p) * capacity), 1)
    tier_a = float(order[k - 1])
    precision, recall, thresholds = precision_recall_curve(y, p)
    ok = np.where(recall[:-1] >= recall_b)[0]
    tier_b = float(thresholds[ok[-1]]) if len(ok) else float(thresholds[0])
    return {"tier_a_threshold": tier_a, "tier_b_threshold": min(tier_b, tier_a)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lightgbm-model", required=True)
    ap.add_argument("--catboost-model", required=True)
    ap.add_argument("--calib-data", required=True)
    ap.add_argument(
        "--tier-a-capacity",
        type=float,
        default=0.02,
        help="fraction of customers the weekly costly-offer capacity covers",
    )
    ap.add_argument("--tier-b-recall", type=float, default=0.80)
    ap.add_argument("--feature-view", default="customer_features")
    ap.add_argument("--candidate-model", required=True)
    args = ap.parse_args()

    lgb_dir, cat_dir = Path(args.lightgbm_model), Path(args.catboost_model)
    params = json.loads((lgb_dir / "params.json").read_text())
    features = params["features"]
    booster = lgb.Booster(model_file=str(lgb_dir / "model.bst"))

    calib = read_split(args.calib_data)
    y = calib[LABEL_COL].astype(int).to_numpy()
    raw = booster.predict(calib[features])
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(raw, y)
    calibrated = iso.predict(raw)

    cfg = {
        "calibrator": {"x": iso.X_thresholds_.tolist(), "y": iso.y_thresholds_.tolist()},
        **tier_thresholds(y, calibrated, args.tier_a_capacity, args.tier_b_recall),
        "features": features,
        "feast_features": [f"{args.feature_view}:{f}" for f in features],
        "reason_codes": {f: REASON_CODES.get(f, f.upper()) for f in features},
    }
    lgb_valid = json.loads((lgb_dir / "metrics.json").read_text())["valid_pr_auc"]
    cat_valid = json.loads((cat_dir / "metrics.json").read_text())["valid_pr_auc"]

    out = Path(args.candidate_model)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(lgb_dir / "model.bst", out / "model.bst")
    with mlflow.start_run() as run:
        cfg["model_version"] = run.info.run_id
        write_json(cfg, out / "calibrator.json")
        mlflow.lightgbm.log_model(booster, artifact_path="model")
        mlflow.log_artifact(str(out / "model.bst"), artifact_path="model")
        mlflow.log_artifact(str(out / "calibrator.json"), artifact_path="model")
        mlflow.log_metrics({"lightgbm_valid_pr_auc": lgb_valid, "catboost_valid_pr_auc": cat_valid})
        write_json(
            {
                "run_id": run.info.run_id,
                "algorithm": "lightgbm",
                "lightgbm_valid_pr_auc": lgb_valid,
                "catboost_valid_pr_auc": cat_valid,
                "challenger_wins": cat_valid > lgb_valid,
            },
            out / "candidate_info.json",
        )


if __name__ == "__main__":
    main()
