import json
import time
import uuid

import pytest

from conftest import BUCKET


def test_predict_known_customer_uses_published_threshold(api, aws, known_customer):
    serving = json.loads(aws["ssm"].get_parameter(Name="/teleconnect-churn/prod/serving-config")["Parameter"]["Value"])
    response = api.post("/v1/predict", json={"customer_id": known_customer})
    assert response.status_code == 200, response.text
    body = response.json()
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["threshold"] == pytest.approx(serving["threshold"])
    assert body["model_version"] == serving["model_version"]
    assert body["churn_flag"] == int(body["churn_probability"] >= body["threshold"])


def test_overrides_move_probability_in_the_expected_direction(api, known_customer):
    risky = {"satisfaction_score": 1, "complaint_count": 5, "contract_type": "Month-to-Month", "tenure_months": 2,
             "avg_days_past_due": 60}
    loyal = {"satisfaction_score": 10, "complaint_count": 0, "contract_type": "Two Year", "tenure_months": 70,
             "avg_days_past_due": 0}
    high = api.post("/v1/predict", json={"customer_id": known_customer, "overrides": risky}).json()
    low = api.post("/v1/predict", json={"customer_id": known_customer, "overrides": loyal}).json()
    assert high["churn_probability"] > low["churn_probability"]


@pytest.mark.parametrize("payload,status", [
    ({"customer_id": "does-not-exist"}, 404),
    ({"customer_id": ""}, 400),
    ({"customer_id": "1", "overrides": {"unknown_feature": 1}}, 400),
])
def test_error_contract(api, payload, status):
    assert api.post("/v1/predict", json=payload).status_code == status


def test_local_p99_latency_under_150ms(api, known_customer):
    latencies = []
    for _ in range(200):
        start = time.perf_counter()
        assert api.post("/v1/predict", json={"customer_id": known_customer}).status_code == 200
        latencies.append((time.perf_counter() - start) * 1000)
    latencies.sort()
    assert latencies[int(0.99 * len(latencies)) - 1] < 150


def _queue_url(aws):
    return aws["sqs"].get_queue_url(QueueName="teleconnect-churn-retrain-triggers")["QueueUrl"]


def _drain(aws, seconds=10):
    url, keys, deadline = _queue_url(aws), [], time.time() + seconds
    while time.time() < deadline:
        for message in aws["sqs"].receive_message(QueueUrl=url, MaxNumberOfMessages=10,
                                                  WaitTimeSeconds=1).get("Messages", []):
            keys.append(json.loads(message["Body"])["detail"]["object"]["key"])
            aws["sqs"].delete_message(QueueUrl=url, ReceiptHandle=message["ReceiptHandle"])
    return keys


def test_one_retrain_trigger_per_data_drop(aws):
    """ADR-5: five source files + manifest must start exactly one retraining run."""
    _drain(aws, seconds=3)
    ingest = f"ingest_date=test-{uuid.uuid4().hex[:8]}"
    for source in ("customers", "billing", "usage", "support", "churn"):
        aws["s3"].put_object(Bucket=BUCKET, Key=f"raw-data/{source}/{ingest}/{source}.csv", Body=b"customer_id\n1\n")
    aws["s3"].put_object(Bucket=BUCKET, Key=f"raw-data/{ingest}/_MANIFEST.json", Body=b"{}")
    keys = [k for k in _drain(aws) if ingest in k]
    assert keys == [f"raw-data/{ingest}/_MANIFEST.json"]


def test_data_lake_is_encrypted_and_versioned(aws):
    encryption = aws["s3"].get_bucket_encryption(Bucket=BUCKET)["ServerSideEncryptionConfiguration"]["Rules"][0]
    assert encryption["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"] == "aws:kms"
    assert aws["s3"].get_bucket_versioning(Bucket=BUCKET)["Status"] == "Enabled"


def test_rollback_and_drift_alarms_exist(aws):
    names = {a["AlarmName"] for page in aws["cloudwatch"].get_paginator("describe_alarms").paginate()
             for a in page["MetricAlarms"]}
    assert {"churn-prod-5xx-rollback", "churn-prod-latency-rollback", "churn-drift-satisfaction_score"} <= names
    topics = [t["TopicArn"] for t in aws["sns"].list_topics()["Topics"]]
    assert any(t.endswith(":customer-churn-alerts") for t in topics)
