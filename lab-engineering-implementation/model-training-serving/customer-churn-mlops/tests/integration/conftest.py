"""Integration tests against the docker-compose stack (LocalStack + model-server + churn-api)."""
import os
import time

import boto3
import httpx
import pytest

API = os.environ.get("CHURN_API_URL", "http://localhost:8080")
BUCKET = os.environ.get("DATA_BUCKET", "teleconnect-churn-local")


def _wait(url: str, timeout: float = 120.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(url, timeout=2).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(2)
    raise RuntimeError(f"{url} not ready after {timeout}s")


@pytest.fixture(scope="session")
def api():
    _wait(f"{API}/readyz")
    with httpx.Client(base_url=API, timeout=5) as client:
        yield client


@pytest.fixture(scope="session")
def aws():
    return {name: boto3.client(name) for name in ("s3", "sqs", "dynamodb", "ssm", "cloudwatch", "sns")}


@pytest.fixture(scope="session")
def known_customer(aws):
    items = aws["dynamodb"].scan(TableName="teleconnect-online-features", Limit=1)["Items"]
    assert items, "online feature table is empty - did the seed container run?"
    return items[0]["customer_id"]["S"]
