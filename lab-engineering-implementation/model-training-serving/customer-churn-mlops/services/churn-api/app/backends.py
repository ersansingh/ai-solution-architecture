"""Feature look-up, model invocation and serving-config backends.

AWS:   Feature Store online store  +  SageMaker endpoint  +  SSM parameter
Local: DynamoDB (LocalStack)       +  HTTP model server   +  SSM parameter (LocalStack)
boto3 honours AWS_ENDPOINT_URL, so the same code talks to LocalStack in docker-compose / k3d.
"""
from __future__ import annotations

import csv
import io
import json
import threading
import time
from typing import Dict, List, Optional, Protocol

import boto3
import httpx
from botocore.config import Config

from app.settings import Settings
from churn import config
from churn.feature_store import from_record


class UnknownCustomer(Exception):
    pass


class ModelUnavailable(Exception):
    pass


class FeatureBackend(Protocol):
    def get(self, customer_id: str) -> Dict[str, object]: ...


class ModelBackend(Protocol):
    def predict(self, rows: List[List[object]], inference_id: Optional[str]) -> List[float]: ...


def _boto_config(timeout: float) -> Config:
    return Config(connect_timeout=timeout, read_timeout=timeout, retries={"max_attempts": 2, "mode": "standard"})


class FeatureStoreBackend:
    def __init__(self, settings: Settings):
        self._client = boto3.client("sagemaker-featurestore-runtime", region_name=settings.region,
                                    config=_boto_config(0.5))
        self._group = settings.feature_group_name

    def get(self, customer_id: str) -> Dict[str, object]:
        response = self._client.get_record(FeatureGroupName=self._group, RecordIdentifierValueAsString=customer_id)
        if "Record" not in response:
            raise UnknownCustomer(customer_id)
        return from_record(response["Record"])


class DynamoDBBackend:
    """Item: {customer_id: S, record: S(JSON list of {FeatureName, ValueAsString})}."""

    def __init__(self, settings: Settings):
        self._client = boto3.client("dynamodb", region_name=settings.region, config=_boto_config(0.5))
        self._table = settings.dynamodb_table

    def get(self, customer_id: str) -> Dict[str, object]:
        item = self._client.get_item(TableName=self._table, Key={"customer_id": {"S": customer_id}}).get("Item")
        if not item:
            raise UnknownCustomer(customer_id)
        return from_record(json.loads(item["record"]["S"]))


def to_csv(rows: List[List[object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for row in rows:
        writer.writerow(["" if v is None else v for v in row])
    return buffer.getvalue()


def parse_probabilities(body: str) -> List[float]:
    return [float(line.split(",")[0]) for line in body.strip().splitlines() if line.strip()]


class SageMakerBackend:
    def __init__(self, settings: Settings, serving: "ServingConfig"):
        self._client = boto3.client("sagemaker-runtime", region_name=settings.region,
                                    config=_boto_config(settings.model_timeout_s))
        self._serving = serving

    def predict(self, rows, inference_id=None):
        kwargs = {"EndpointName": self._serving.current()["endpoint_name"], "ContentType": "text/csv",
                  "Accept": "text/csv", "Body": to_csv(rows)}
        if inference_id:
            kwargs["InferenceId"] = inference_id
        try:
            response = self._client.invoke_endpoint(**kwargs)
        except Exception as exc:  # noqa: BLE001 - any transport/model error is a 503 for the caller
            raise ModelUnavailable(str(exc)) from exc
        return parse_probabilities(response["Body"].read().decode())


class HttpModelBackend:
    def __init__(self, settings: Settings):
        self._client = httpx.Client(base_url=settings.model_server_url, timeout=settings.model_timeout_s)

    def predict(self, rows, inference_id=None):
        try:
            response = self._client.post("/invocations", content=to_csv(rows),
                                         headers={"Content-Type": "text/csv", "Accept": "text/csv"})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ModelUnavailable(str(exc)) from exc
        return parse_probabilities(response.text)


class ServingConfig:
    """Threshold / model version / endpoint published by the deploy state machine (SSM), cached."""

    def __init__(self, settings: Settings, ssm_client=None):
        self._settings = settings
        self._ssm = ssm_client
        self._value: Optional[dict] = None
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    def _fallback(self) -> dict:
        return {"endpoint_name": self._settings.endpoint_name, "threshold": self._settings.default_threshold,
                "model_version": "unknown", "source": "defaults"}

    def current(self) -> dict:
        now = time.monotonic()
        if self._value is not None and now - self._loaded_at < self._settings.serving_config_ttl_s:
            return self._value
        with self._lock:
            try:
                ssm = self._ssm or boto3.client("ssm", region_name=self._settings.region, config=_boto_config(0.5))
                raw = ssm.get_parameter(Name=self._settings.serving_config_parameter)["Parameter"]["Value"]
                self._value = {**self._fallback(), **json.loads(raw), "source": "ssm"}
            except Exception:  # noqa: BLE001 - keep serving with the last good (or default) config
                if self._value is None:
                    self._value = self._fallback()
            self._loaded_at = now
            return self._value


def build_backends(settings: Settings):
    serving = ServingConfig(settings)
    features = DynamoDBBackend(settings) if settings.feature_backend == "dynamodb" else FeatureStoreBackend(settings)
    model = HttpModelBackend(settings) if settings.model_backend == "http" else SageMakerBackend(settings, serving)
    return features, model, serving


def model_input_columns() -> List[str]:
    return config.model_input_columns()


def apply_overrides(record: Dict[str, object], overrides: Dict[str, object]) -> Dict[str, object]:
    """What-if scoring: apply raw overrides, then recompute the engineered features from them."""
    if not overrides:
        return record
    import pandas as pd  # only needed on the override path

    from churn.feature_engineering import add_engineered_features

    frame = pd.DataFrame([{**record, **overrides}])
    numeric = config.numeric_columns()
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    row = add_engineered_features(frame).iloc[0].to_dict()
    # Explicit overrides of engineered features win over the recomputed value.
    row.update(overrides)
    return {c: (None if pd.isna(row.get(c)) else row.get(c)) for c in model_input_columns()}
