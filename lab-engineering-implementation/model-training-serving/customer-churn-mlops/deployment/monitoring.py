"""M7: Model Monitor schedules for the production endpoint (plan section 6.6).

  python deployment/monitoring.py --endpoint customer-churn-prod
    - Data quality: daily, baseline = DriftCheckBaselines of the deployed model package,
      CloudWatch metrics on (feature_baseline_drift_<feature> in aws/sagemaker/Endpoints/data-metrics)
    - Model quality: daily, merges captured predictions with ground truth written by
      deployment/ground_truth.py (labels arrive ~90 days after prediction; plan G12)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from churn import config  # noqa: E402


def deployed_package(sm, endpoint: str) -> dict:
    endpoint_config = sm.describe_endpoint(EndpointName=endpoint)["EndpointConfigName"]
    model_name = sm.describe_endpoint_config(EndpointConfigName=endpoint_config)["ProductionVariants"][0]["ModelName"]
    containers = sm.describe_model(ModelName=model_name).get("Containers", [])
    arn = next(c["ModelPackageName"] for c in containers if "ModelPackageName" in c)
    return sm.describe_model_package(ModelPackageName=arn)


def main() -> None:
    from sagemaker.model_monitor import (
        CronExpressionGenerator,
        DefaultModelMonitor,
        EndpointInput,
        ModelQualityMonitor,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=config.project()["endpoints"]["prod"])
    args = parser.parse_args()
    cfg = config.project()
    sm, ssm = boto3.client("sagemaker"), boto3.client("ssm")
    package = deployed_package(sm, args.endpoint)
    baselines = package["DriftCheckBaselines"]["ModelDataQuality"]
    serving = json.loads(ssm.get_parameter(Name=cfg["serving_config_parameter"].format(stage="prod"))
                         ["Parameter"]["Value"])

    data_quality = DefaultModelMonitor(role=cfg["sagemaker_role_arn"], instance_count=1,
                                       instance_type="ml.m5.xlarge", volume_size_in_gb=50,
                                       max_runtime_in_seconds=3600)
    data_quality.create_monitoring_schedule(
        monitor_schedule_name=f"{args.endpoint}-data-quality",
        endpoint_input=args.endpoint,
        output_s3_uri=config.s3_uri("monitoring", "reports", "data-quality"),
        statistics=baselines["Statistics"]["S3Uri"],
        constraints=baselines["Constraints"]["S3Uri"],
        schedule_cron_expression=CronExpressionGenerator.daily(),
        enable_cloudwatch_metrics=True,
    )

    model_quality = ModelQualityMonitor(role=cfg["sagemaker_role_arn"], instance_count=1,
                                        instance_type="ml.m5.xlarge", volume_size_in_gb=50,
                                        max_runtime_in_seconds=3600)
    model_quality.create_monitoring_schedule(
        monitor_schedule_name=f"{args.endpoint}-model-quality",
        endpoint_input=EndpointInput(endpoint_name=args.endpoint,
                                     destination="/opt/ml/processing/input_data",
                                     probability_attribute="0",
                                     probability_threshold_attribute=float(serving["threshold"])),
        ground_truth_input=config.s3_uri("monitoring", "ground-truth"),
        problem_type="BinaryClassification",
        output_s3_uri=config.s3_uri("monitoring", "reports", "model-quality"),
        schedule_cron_expression=CronExpressionGenerator.daily(),
        enable_cloudwatch_metrics=True,
    )
    print(f"monitoring schedules created for {args.endpoint}")


if __name__ == "__main__":
    main()
