"""Runtime settings (environment variables; Helm values map onto these)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    stage: str = field(default_factory=lambda: os.environ.get("STAGE", "prod"))
    region: str = field(default_factory=lambda: os.environ.get("AWS_REGION", "us-east-1"))
    # featurestore (AWS) | dynamodb (LocalStack stand-in for the online store)
    feature_backend: str = field(default_factory=lambda: os.environ.get("FEATURE_BACKEND", "featurestore"))
    feature_group_name: str = field(default_factory=lambda: os.environ.get(
        "FEATURE_GROUP_NAME", "teleconnect-customer-features"))
    dynamodb_table: str = field(default_factory=lambda: os.environ.get("DYNAMODB_TABLE", "teleconnect-online-features"))
    # sagemaker (AWS) | http (local model server speaking the SageMaker container contract)
    model_backend: str = field(default_factory=lambda: os.environ.get("MODEL_BACKEND", "sagemaker"))
    endpoint_name: str = field(default_factory=lambda: os.environ.get("ENDPOINT_NAME", "customer-churn-prod"))
    model_server_url: str = field(default_factory=lambda: os.environ.get(
        "MODEL_SERVER_URL", "http://model-server:8080"))
    serving_config_parameter: str = field(default_factory=lambda: os.environ.get(
        "SERVING_CONFIG_PARAMETER", "/teleconnect-churn/prod/serving-config"))
    serving_config_ttl_s: int = field(default_factory=lambda: int(os.environ.get("SERVING_CONFIG_TTL_S", "60")))
    default_threshold: float = field(default_factory=lambda: float(os.environ.get("DEFAULT_THRESHOLD", "0.5")))
    model_timeout_s: float = field(default_factory=lambda: float(os.environ.get("MODEL_TIMEOUT_S", "1.0")))
    metrics_enabled: bool = field(default_factory=lambda: _bool("METRICS_ENABLED", False))
    metrics_namespace: str = field(default_factory=lambda: os.environ.get("METRICS_NAMESPACE", "TeleConnect/Churn"))
    metrics_interval_s: int = field(default_factory=lambda: int(os.environ.get("METRICS_INTERVAL_S", "60")))
