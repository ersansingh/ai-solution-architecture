import io
import json

import pytest
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber

import handlers

STAGES = {
    "staging": {"endpoint_name": "customer-churn-staging", "instance_type": "ml.c5.large", "instance_count": 1,
                "min_capacity": 1, "max_capacity": 1, "target_invocations": 100, "strategy": "rolling",
                "capture_pct": 100, "rollback_alarms": []},
    "prod": {"endpoint_name": "customer-churn-prod", "instance_type": "ml.c5.large", "instance_count": 2,
             "min_capacity": 2, "max_capacity": 6, "target_invocations": 300, "strategy": "blue_green_canary",
             "capture_pct": 20, "rollback_alarms": ["churn-prod-5xx-rollback", "churn-prod-latency-rollback"]},
}
ARN = "arn:aws:sagemaker:us-east-1:123456789012:model-package/customer-churn-models/7"
EP_ARN = "arn:aws:sagemaker:us-east-1:123456789012:endpoint/customer-churn-prod"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("STAGE_CONFIG", json.dumps(STAGES))
    monkeypatch.setenv("ENDPOINT_ROLE_ARN", "arn:aws:iam::123456789012:role/endpoint")
    monkeypatch.setenv("DATA_CAPTURE_S3_URI", "s3://bucket/monitoring/data-capture")
    monkeypatch.setenv("SERVING_CONFIG_PARAMETER", "/teleconnect-churn/{stage}/serving-config")
    monkeypatch.setenv("DATA_BUCKET", "bucket")
    handlers._clients.clear()
    yield
    handlers._clients.clear()


def _stub(name):
    stubber = Stubber(handlers.client(name))
    stubber.activate()
    return stubber


def test_deployment_config_prod_is_canary_with_rollback_alarms():
    cfg = handlers.deployment_config(STAGES["prod"])
    routing = cfg["BlueGreenUpdatePolicy"]["TrafficRoutingConfiguration"]
    assert routing["Type"] == "CANARY" and routing["CanarySize"]["Value"] == 10
    assert [a["AlarmName"] for a in cfg["AutoRollbackConfiguration"]["Alarms"]] == STAGES["prod"]["rollback_alarms"]


def test_deployment_config_staging_is_rolling_without_empty_alarm_list():
    cfg = handlers.deployment_config(STAGES["staging"])
    assert "RollingUpdatePolicy" in cfg and "AutoRollbackConfiguration" not in cfg


def test_deploy_updates_existing_prod_endpoint_blue_green():
    sm, aas = _stub("sagemaker"), _stub("application-autoscaling")
    sm.add_response("describe_model_package", {"ModelPackageName": "p", "ModelPackageArn": ARN,
                                               "ModelPackageVersion": 7, "CreationTime": "2026-10-01",
                                               "ModelPackageStatus": "Completed",
                                               "ModelPackageStatusDetails": {"ValidationStatuses": [],
                                                                             "ImageScanStatuses": []}},
                    {"ModelPackageName": ARN})
    sm.add_response("create_model", {"ModelArn": EP_ARN.replace("endpoint", "model")},
                    {"ModelName": ANY, "ExecutionRoleArn": ANY, "Containers": [{"ModelPackageName": ARN}]})
    sm.add_response("create_endpoint_config", {"EndpointConfigArn": EP_ARN.replace("endpoint", "endpoint-config")},
                    {"EndpointConfigName": ANY, "ProductionVariants": ANY, "DataCaptureConfig": ANY})
    sm.add_response("describe_endpoint", {"EndpointName": "customer-churn-prod", "EndpointArn": EP_ARN,
                                          "EndpointConfigName": "old", "EndpointStatus": "InService",
                                          "CreationTime": "2026-10-01", "LastModifiedTime": "2026-10-01"},
                    {"EndpointName": "customer-churn-prod"})
    aas.add_response("describe_scalable_targets", {"ScalableTargets": [{
        "ServiceNamespace": "sagemaker", "ResourceId": "endpoint/customer-churn-prod/variant/AllTraffic",
        "ScalableDimension": "sagemaker:variant:DesiredInstanceCount", "MinCapacity": 2, "MaxCapacity": 6,
        "RoleARN": "arn:aws:iam::123456789012:role/aas", "CreationTime": "2026-10-01"}]},
        {"ServiceNamespace": "sagemaker", "ResourceIds": ANY})
    aas.add_response("deregister_scalable_target", {}, {"ServiceNamespace": "sagemaker", "ResourceId": ANY,
                                                        "ScalableDimension": ANY})
    sm.add_response("update_endpoint", {"EndpointArn": EP_ARN},
                    {"EndpointName": "customer-churn-prod", "EndpointConfigName": ANY, "DeploymentConfig": ANY})
    out = handlers.deploy_endpoint({"stage": "prod", "model_package_arn": ARN})
    assert out["action"] == "update" and out["model_version"] == 7
    assert out["endpoint_config_name"].startswith("churn-prod-v7-")
    sm.assert_no_pending_responses()


def test_status_detects_automatic_rollback():
    sm = _stub("sagemaker")
    sm.add_response("describe_endpoint", {"EndpointName": "e", "EndpointArn": EP_ARN, "EndpointConfigName": "old",
                                          "EndpointStatus": "InService", "CreationTime": "2026-10-01",
                                          "LastModifiedTime": "2026-10-01"}, {"EndpointName": "e"})
    out = handlers.endpoint_status({"endpoint_name": "e", "endpoint_config_name": "new"})
    assert out["rolled_back"] is True and out["in_progress"] is False


def test_publish_serving_config_reads_threshold_from_registry_metrics():
    sm, s3, ssm = _stub("sagemaker"), _stub("s3"), _stub("ssm")
    sm.add_response("describe_model_package", {
        "ModelPackageName": "p", "ModelPackageArn": ARN, "ModelPackageVersion": 7, "CreationTime": "2026-10-01",
        "ModelPackageStatus": "Completed",
        "ModelPackageStatusDetails": {"ValidationStatuses": [], "ImageScanStatuses": []},
        "ModelMetrics": {"ModelQuality": {"Statistics": {
            "ContentType": "application/json", "S3Uri": "s3://bucket/artifacts/x/evaluation.json"}}}},
        {"ModelPackageName": ARN})
    body = json.dumps({"threshold": 0.73, "binary_classification_metrics": {"auc": {"value": 0.98}}}).encode()
    s3.add_response("get_object", {"Body": StreamingBody(io.BytesIO(body), len(body))},
                    {"Bucket": "bucket", "Key": "artifacts/x/evaluation.json"})
    ssm.add_response("put_parameter", {"Version": 1}, {"Name": "/teleconnect-churn/prod/serving-config",
                                                       "Value": ANY, "Type": "String", "Overwrite": True})
    out = handlers.publish_serving_config({"stage": "prod", "model_package_arn": ARN,
                                           "endpoint_name": "customer-churn-prod"})
    assert out["serving_config"]["threshold"] == 0.73 and out["serving_config"]["model_version"] == 7
