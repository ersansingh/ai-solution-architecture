"""M3: train the four required algorithms on the pipeline's preprocessed splits and track
every job as a SageMaker Experiments run (plan section 6.2).

  python -m churn.experiments.train_models --data s3://<bucket>/training/<dataset_version>
     [--lightgbm-image <account>.dkr.ecr.<region>.amazonaws.com/churn-lightgbm:<tag>] [--wait]
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime

import sagemaker
from sagemaker import image_uris
from sagemaker.estimator import Estimator
from sagemaker.experiments.run import Run
from sagemaker.inputs import TrainingInput
from sagemaker.sklearn.estimator import SKLearn

from churn import config

METRICS = [
    {"Name": "validation:auc", "Regex": r"validation:auc=([0-9\.]+)"},
    {"Name": "validation:precision", "Regex": r"validation:precision=([0-9\.]+)"},
    {"Name": "validation:recall", "Regex": r"validation:recall=([0-9\.]+)"},
]


def estimators(session, role, output_path, lightgbm_image):
    cfg = config.project()
    region = session.boto_region_name
    itype = cfg["instance_types"]["training"]
    hp = config.best_hparams()

    xgb = Estimator(image_uris.retrieve("xgboost", region, cfg["framework_versions"]["xgboost"]),
                    role, instance_count=1, instance_type=itype, output_path=output_path,
                    use_spot_instances=True, max_run=3600, max_wait=7200,
                    checkpoint_s3_uri=f"{output_path}/checkpoints/xgboost", sagemaker_session=session)
    xgb.set_hyperparameters(**hp)

    linear = Estimator(image_uris.retrieve("linear-learner", region), role, instance_count=1,
                       instance_type=itype, output_path=output_path, sagemaker_session=session)
    linear.set_hyperparameters(  # plan G5
        predictor_type="binary_classifier", epochs=15, mini_batch_size=1000,
        positive_example_weight_mult="balanced",
        binary_classifier_model_selection_criteria="precision_at_target_recall", target_recall=0.8,
    )

    rf = SKLearn(entry_point="train_rf.py", source_dir=os.path.dirname(os.path.dirname(__file__)),
                 framework_version=cfg["framework_versions"]["sklearn"], role=role, instance_type=itype,
                 output_path=output_path, metric_definitions=METRICS, sagemaker_session=session,
                 hyperparameters={"n-estimators": 300, "max-depth": 16, "min-samples-leaf": 20})

    models = {"xgboost": xgb, "linear-learner": linear, "random-forest": rf}
    if lightgbm_image:  # plan G6: BYOC image from containers/lightgbm
        models["lightgbm"] = Estimator(lightgbm_image, role, instance_count=1, instance_type=itype,
                                       output_path=output_path, metric_definitions=METRICS,
                                       hyperparameters={"num_leaves": 63, "learning_rate": 0.05,
                                                        "num_boost_round": 500},
                                       sagemaker_session=session)
    return models


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="S3 prefix containing train/ and validation/")
    parser.add_argument("--lightgbm-image", default="")
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()

    cfg = config.project()
    session = sagemaker.Session()
    role = cfg["sagemaker_role_arn"] or sagemaker.get_execution_role()
    output_path = config.s3_uri("models", "experiments")
    channels = {
        "train": TrainingInput(f"{args.data}/train/", content_type="text/csv"),
        "validation": TrainingInput(f"{args.data}/validation/", content_type="text/csv"),
    }
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    for name, estimator in estimators(session, role, output_path, args.lightgbm_image).items():
        with Run(experiment_name=cfg["experiment_name"], run_name=f"{name}-{stamp}", sagemaker_session=session) as run:
            run.log_parameters({"algorithm": name, "dataset": args.data})
            estimator.fit(channels, job_name=f"churn-{name}-{stamp}", wait=args.wait)
            run.log_parameter("training_job", estimator.latest_training_job.name)


if __name__ == "__main__":
    main()
