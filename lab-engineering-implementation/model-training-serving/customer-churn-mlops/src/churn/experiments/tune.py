"""M4: Bayesian HPO for XGBoost on validation:auc (plan section 6.2, G7) and write the
winning hyperparameters to config/best_hparams.json for the monthly pipeline.

  python -m churn.experiments.tune --data s3://<bucket>/training/<dataset_version> [--max-jobs 30]
"""
from __future__ import annotations

import argparse
import json

import sagemaker
from sagemaker import image_uris
from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput
from sagemaker.tuner import ContinuousParameter, HyperparameterTuner, IntegerParameter

from churn import config

RANGES = {
    "eta": ContinuousParameter(0.01, 0.3, scaling_type="Logarithmic"),
    "max_depth": IntegerParameter(3, 10),
    "num_round": IntegerParameter(100, 500),
    "min_child_weight": IntegerParameter(1, 10),
    "gamma": ContinuousParameter(0, 10),
    "subsample": ContinuousParameter(0.5, 1.0),
    "alpha": ContinuousParameter(0, 10),
    "lambda": ContinuousParameter(0, 10),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--max-jobs", type=int, default=30)
    parser.add_argument("--max-parallel-jobs", type=int, default=5)
    args = parser.parse_args()

    cfg = config.project()
    session = sagemaker.Session()
    role = cfg["sagemaker_role_arn"] or sagemaker.get_execution_role()
    estimator = Estimator(
        image_uris.retrieve("xgboost", session.boto_region_name, cfg["framework_versions"]["xgboost"]),
        role, instance_count=1, instance_type=cfg["instance_types"]["training"],
        output_path=config.s3_uri("models", "tuning"), sagemaker_session=session,
    )
    fixed = {k: v for k, v in config.best_hparams().items() if k not in RANGES}
    estimator.set_hyperparameters(**fixed)
    tuner = HyperparameterTuner(
        estimator, objective_metric_name="validation:auc", objective_type="Maximize",
        hyperparameter_ranges=RANGES, strategy="Bayesian", early_stopping_type="Auto",
        max_jobs=args.max_jobs, max_parallel_jobs=args.max_parallel_jobs,
    )
    tuner.fit({
        "train": TrainingInput(f"{args.data}/train/", content_type="text/csv"),
        "validation": TrainingInput(f"{args.data}/validation/", content_type="text/csv"),
    })
    best = session.sagemaker_client.describe_training_job(TrainingJobName=tuner.best_training_job())
    tuned = {k: v for k, v in best["HyperParameters"].items() if not k.startswith("_") and "sagemaker" not in k}
    path = config.config_dir() / "best_hparams.json"
    path.write_text(json.dumps({**fixed, **tuned}, indent=2) + "\n")
    print(f"best job {tuner.best_training_job()} -> {path}")


if __name__ == "__main__":
    main()
