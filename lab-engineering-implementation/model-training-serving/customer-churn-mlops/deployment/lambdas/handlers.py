"""Lambda handlers used by the deploy state machine (deployment/stepfunctions/deploy.asl.json).

One zip, five functions (plan section 6.7, ADR-6/ADR-7):
  deploy_endpoint         create model + endpoint config; create or update the endpoint
                          (staging: rolling update, prod: blue/green canary with auto rollback)
  endpoint_status         poll status and detect an automatic rollback
  configure_autoscaling   target tracking on InvocationsPerInstance (prod)
  smoke_test              golden records through the endpoint: validity, sanity accuracy, p99 latency
  publish_serving_config  SSM parameter read by churn-api (threshold, model version, endpoint)

Environment:
  STAGE_CONFIG              JSON {stage: {endpoint_name, instance_type, instance_count, min_capacity,
                            max_capacity, target_invocations, strategy, capture_pct, rollback_alarms}}
  ENDPOINT_ROLE_ARN         SageMaker execution role for the model
  DATA_CAPTURE_S3_URI       s3://<bucket>/monitoring/data-capture
  KMS_KEY_ARN               optional, for data capture + endpoint volumes
  SERVING_CONFIG_PARAMETER  e.g. /teleconnect-churn/{stage}/serving-config
  VARIANT_NAME              default AllTraffic
"""
from __future__ import annotations

import csv
import io
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

VARIANT = os.environ.get("VARIANT_NAME", "AllTraffic")
IN_PROGRESS = {"Creating", "Updating", "SystemUpdating", "RollingBack"}

_clients = {}


def client(name):
    if name not in _clients:
        _clients[name] = boto3.client(name)
    return _clients[name]


def stage_config(stage: str) -> dict:
    return json.loads(os.environ["STAGE_CONFIG"])[stage]


def _package(arn: str) -> dict:
    return client("sagemaker").describe_model_package(ModelPackageName=arn)


def _read_s3(uri: str) -> bytes:
    parsed = urlparse(uri)
    return client("s3").get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))["Body"].read()


def _endpoint_exists(name: str) -> bool:
    try:
        client("sagemaker").describe_endpoint(EndpointName=name)
        return True
    except ClientError as exc:
        if "Could not find endpoint" in str(exc):
            return False
        raise


def deployment_config(cfg: dict) -> dict:
    """Staging: rolling update (Lab Part 9). Prod: blue/green canary 10% -> 100% (plan G15, ADR-7)."""
    if cfg.get("strategy") == "rolling":
        config = {"RollingUpdatePolicy": {
            "MaximumBatchSize": {"Type": "INSTANCE_COUNT", "Value": 1},
            "WaitIntervalInSeconds": 120,
            "MaximumExecutionTimeoutInSeconds": 3600,
            "RollbackMaximumBatchSize": {"Type": "INSTANCE_COUNT", "Value": 1},
        }}
    else:
        config = {"BlueGreenUpdatePolicy": {
            "TrafficRoutingConfiguration": {
                "Type": "CANARY",
                "CanarySize": {"Type": "CAPACITY_PERCENT", "Value": 10},
                "WaitIntervalInSeconds": 600,
            },
            "TerminationWaitInSeconds": 300,
            "MaximumExecutionTimeoutInSeconds": 3600,
        }}
    alarms = cfg.get("rollback_alarms", [])
    if alarms:
        config["AutoRollbackConfiguration"] = {"Alarms": [{"AlarmName": a} for a in alarms]}
    return config


def deploy_endpoint(event, _context=None):
    stage, arn = event["stage"], event["model_package_arn"]
    cfg = stage_config(stage)
    sm = client("sagemaker")
    version = _package(arn)["ModelPackageVersion"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    name = f"churn-{stage}-v{version}-{stamp}"

    sm.create_model(ModelName=name, ExecutionRoleArn=os.environ["ENDPOINT_ROLE_ARN"],
                    Containers=[{"ModelPackageName": arn}])
    capture = {
        "EnableCapture": True,
        "InitialSamplingPercentage": int(cfg.get("capture_pct", 100)),
        "DestinationS3Uri": os.environ["DATA_CAPTURE_S3_URI"],
        "CaptureOptions": [{"CaptureMode": "Input"}, {"CaptureMode": "Output"}],
        "CaptureContentTypeHeader": {"CsvContentTypes": ["text/csv"]},
    }
    variant = {"VariantName": VARIANT, "ModelName": name, "InitialInstanceCount": int(cfg["instance_count"]),
               "InstanceType": cfg["instance_type"], "InitialVariantWeight": 1.0}
    config_args = {"EndpointConfigName": name, "ProductionVariants": [variant], "DataCaptureConfig": capture}
    if os.environ.get("KMS_KEY_ARN"):
        config_args["KmsKeyId"] = os.environ["KMS_KEY_ARN"]
        capture["KmsKeyId"] = os.environ["KMS_KEY_ARN"]
    sm.create_endpoint_config(**config_args)

    endpoint = cfg["endpoint_name"]
    if _endpoint_exists(endpoint):
        # Auto scaling must be detached while the variant fleet is replaced; re-attached afterwards.
        _deregister_autoscaling(endpoint)
        sm.update_endpoint(EndpointName=endpoint, EndpointConfigName=name,
                           DeploymentConfig=deployment_config(cfg))
        action = "update"
    else:
        sm.create_endpoint(EndpointName=endpoint, EndpointConfigName=name,
                           Tags=[{"Key": "project", "Value": "teleconnect-churn"}, {"Key": "env", "Value": stage}])
        action = "create"
    return {**event, "endpoint_name": endpoint, "endpoint_config_name": name, "model_version": version,
            "action": action}


def _deregister_autoscaling(endpoint: str) -> None:
    aas = client("application-autoscaling")
    resource = f"endpoint/{endpoint}/variant/{VARIANT}"
    targets = aas.describe_scalable_targets(ServiceNamespace="sagemaker", ResourceIds=[resource])
    if targets["ScalableTargets"]:
        aas.deregister_scalable_target(ServiceNamespace="sagemaker", ResourceId=resource,
                                       ScalableDimension="sagemaker:variant:DesiredInstanceCount")


def endpoint_status(event, _context=None):
    detail = client("sagemaker").describe_endpoint(EndpointName=event["endpoint_name"])
    status = detail["EndpointStatus"]
    rolled_back = status == "InService" and detail["EndpointConfigName"] != event["endpoint_config_name"]
    return {**event, "status": status, "in_progress": status in IN_PROGRESS, "rolled_back": rolled_back,
            "failure_reason": detail.get("FailureReason", "")}


def configure_autoscaling(event, _context=None):
    cfg = stage_config(event["stage"])
    if int(cfg.get("max_capacity", 0)) <= int(cfg["instance_count"]):
        return {**event, "autoscaling": "skipped"}
    aas = client("application-autoscaling")
    resource = f"endpoint/{event['endpoint_name']}/variant/{VARIANT}"
    aas.register_scalable_target(ServiceNamespace="sagemaker", ResourceId=resource,
                                 ScalableDimension="sagemaker:variant:DesiredInstanceCount",
                                 MinCapacity=int(cfg["min_capacity"]), MaxCapacity=int(cfg["max_capacity"]))
    aas.put_scaling_policy(
        PolicyName=f"{event['endpoint_name']}-invocations", ServiceNamespace="sagemaker", ResourceId=resource,
        ScalableDimension="sagemaker:variant:DesiredInstanceCount", PolicyType="TargetTrackingScaling",
        TargetTrackingScalingPolicyConfiguration={
            "TargetValue": float(cfg["target_invocations"]),
            "PredefinedMetricSpecification": {"PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"},
            "ScaleInCooldown": 300, "ScaleOutCooldown": 60,
        },
    )
    return {**event, "autoscaling": "configured"}


def golden_records(model_package_arn: str, limit: int = 50):
    """Rows from the test_raw split of the pipeline run that produced this package."""
    meta = _package(model_package_arn).get("CustomerMetadataProperties", {})
    bucket = os.environ["DATA_BUCKET"]
    uri = f"s3://{bucket}/training/{meta['dataset_version']}/test_raw/test_raw.csv"
    rows = list(csv.reader(io.StringIO(_read_s3(uri).decode())))
    header, body = rows[0], rows[1:limit + 1]
    return header, body


def smoke_test(event, _context=None):
    header, rows = golden_records(event["model_package_arn"])
    runtime = client("sagemaker-runtime")
    latencies, correct, invalid = [], 0, 0
    for row in rows:
        features, label = row[1:-1], int(row[-1])
        start = time.perf_counter()
        response = runtime.invoke_endpoint(EndpointName=event["endpoint_name"], ContentType="text/csv",
                                           Body=",".join(features))
        latencies.append((time.perf_counter() - start) * 1000)
        probability = float(response["Body"].read().decode().strip().split("\n")[0])
        if not 0.0 <= probability <= 1.0:
            invalid += 1
        correct += int((probability >= 0.5) == bool(label))
    latencies.sort()
    p99 = latencies[min(len(latencies) - 1, int(0.99 * len(latencies)))]
    accuracy = correct / max(len(rows), 1)
    budget = float(os.environ.get("LATENCY_BUDGET_MS", "150"))
    passed = invalid == 0 and accuracy >= 0.8 and p99 <= budget
    return {**event, "smoke": {"passed": passed, "records": len(rows), "accuracy": round(accuracy, 3),
                               "p99_ms": round(p99, 1), "invalid": invalid}}


def publish_serving_config(event, _context=None):
    package = _package(event["model_package_arn"])
    stats_uri = package["ModelMetrics"]["ModelQuality"]["Statistics"]["S3Uri"]
    evaluation = json.loads(_read_s3(stats_uri))
    value = {
        "endpoint_name": event["endpoint_name"],
        "model_package_arn": event["model_package_arn"],
        "model_version": package["ModelPackageVersion"],
        "threshold": evaluation["threshold"],
        "auc": evaluation["binary_classification_metrics"]["auc"]["value"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    name = os.environ["SERVING_CONFIG_PARAMETER"].format(stage=event["stage"])
    client("ssm").put_parameter(Name=name, Value=json.dumps(value), Type="String", Overwrite=True)
    return {**event, "serving_config": value}
