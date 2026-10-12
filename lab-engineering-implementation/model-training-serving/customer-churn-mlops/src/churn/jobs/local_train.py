"""Local end-to-end run (no AWS): generate -> preprocess -> train XGBoost -> evaluate.

Produces the artifacts the local stack serves (services/model-server) and seeds
LocalStack with (scripts/seed_localstack.py):
  <work>/processed/...            outputs of jobs.preprocess
  <work>/model/xgboost-model      booster trained with config/best_hparams.json
  <work>/model/preprocessor.joblib, feature_contract.json
  <work>/evaluation/evaluation.json

Usage: python -m churn.jobs.local_train --rows 200000 --work ./local/work
"""
from __future__ import annotations

import argparse
import json
import os
import shutil

import xgboost as xgb

from churn import config
from churn.data.generate_synthetic import generate
from churn.jobs import evaluate as evaluate_job
from churn.jobs import preprocess

# Built-in-algorithm hyperparameters that are not xgboost.train() params.
_NON_PARAMS = {"num_round"}


def train_xgboost(train_csv: str, validation_csv: str, model_dir: str, hparams: dict) -> xgb.Booster:
    x_train, y_train = evaluate_job.load_split(train_csv)
    x_val, y_val = evaluate_job.load_split(validation_csv)
    dtrain, dval = xgb.DMatrix(x_train, label=y_train), xgb.DMatrix(x_val, label=y_val)
    params = {k: (float(v) if k not in ("objective", "eval_metric") else v)
              for k, v in hparams.items() if k not in _NON_PARAMS}
    params["max_depth"] = int(params["max_depth"])
    booster = xgb.train(params, dtrain, num_boost_round=int(hparams["num_round"]),
                        evals=[(dval, "validation")], early_stopping_rounds=30, verbose_eval=50)
    os.makedirs(model_dir, exist_ok=True)
    booster.save_model(os.path.join(model_dir, "xgboost-model"))
    return booster


def run(rows: int, work: str, ingest_date: str = "2026-10-01") -> dict:
    data_root = os.path.join(work, "data")
    if not os.path.exists(os.path.join(data_root, "raw-data")):
        generate(rows, data_root, ingest_date)
    processed = os.path.join(work, "processed")
    report = preprocess.run(data_root, processed)
    model_dir = os.path.join(work, "model")
    train_xgboost(f"{processed}/train/train.csv", f"{processed}/validation/validation.csv",
                  model_dir, config.best_hparams())
    for name in ("preprocessor.joblib", "feature_contract.json"):
        shutil.copy(os.path.join(processed, "model", name), os.path.join(model_dir, name))
    gates = config.quality_gates()
    metrics = evaluate_job.run(model_dir, f"{processed}/validation/validation.csv",
                               f"{processed}/test/test.csv", os.path.join(work, "evaluation"), gates)
    return {"data_quality": report, "threshold": metrics["threshold"], "gates": metrics["gates"],
            "metrics": {k: v["value"] for k, v in metrics["binary_classification_metrics"].items() if "value" in v}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=200_000)
    parser.add_argument("--work", default="./local/work")
    args = parser.parse_args()
    print(json.dumps(run(args.rows, args.work), indent=2))


if __name__ == "__main__":
    main()
