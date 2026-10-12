"""churn-api: real-time churn scoring service on EKS (plan section 6.3).

POST /v1/predict {"customer_id": "100042", "overrides": {...optional}}
  -> Feature Store GetRecord -> SageMaker endpoint (PipelineModel) -> threshold from SSM
GET  /healthz  liveness      GET /readyz  readiness (serving config resolved)
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Optional, Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.backends import ModelUnavailable, UnknownCustomer, apply_overrides, build_backends, model_input_columns
from app.metrics import MetricsPublisher
from app.settings import Settings

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
log = logging.getLogger("churn-api")


class PredictRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    overrides: Dict[str, Union[float, str, None]] = Field(default_factory=dict)


class PredictResponse(BaseModel):
    customer_id: str
    churn_probability: float
    churn_flag: int
    threshold: float
    model_version: str
    latency_ms: float


def _hash(customer_id: str) -> str:
    """Customer ids are not logged in clear text (plan section 10)."""
    return hashlib.sha256(customer_id.encode()).hexdigest()[:12]


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


def create_app(settings: Optional[Settings] = None, features=None, model=None, serving=None) -> FastAPI:
    settings = settings or Settings()
    if features is None or model is None or serving is None:
        built = build_backends(settings)
        features, model, serving = features or built[0], model or built[1], serving or built[2]
    columns = model_input_columns()
    allowed = set(columns)
    metrics = MetricsPublisher(settings.metrics_namespace, settings.stage, settings.metrics_interval_s,
                               settings.region, settings.metrics_enabled)

    @asynccontextmanager
    async def lifespan(_app):
        serving.current()
        metrics.start()
        yield
        metrics.stop()

    app = FastAPI(title="TeleConnect churn API", version="1.0.0", lifespan=lifespan)
    app.state.metrics = metrics

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        return _error(400, "invalid_request", json.dumps(exc.errors(), default=str))

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz():
        current = serving.current()
        return {"status": "ready", "model_version": str(current.get("model_version")),
                "config_source": current.get("source")}

    @app.post("/v1/predict", response_model=PredictResponse)
    def predict(body: PredictRequest):
        started = time.perf_counter()
        unknown = sorted(set(body.overrides) - allowed)
        if unknown:
            return _error(400, "invalid_overrides", f"unknown features: {unknown}")
        try:
            record = features.get(body.customer_id)
        except UnknownCustomer:
            metrics.record((time.perf_counter() - started) * 1000, error=True)
            return _error(404, "unknown_customer", "no features for this customer_id")
        record = apply_overrides(record, body.overrides)
        current = serving.current()
        inference_id = f"{body.customer_id}:{datetime.now(timezone.utc):%Y%m%d}"
        try:
            probability = model.predict([[record.get(c) for c in columns]], inference_id)[0]
        except ModelUnavailable as exc:
            latency = (time.perf_counter() - started) * 1000
            metrics.record(latency, error=True)
            log.error(json.dumps({"event": "model_unavailable", "customer": _hash(body.customer_id),
                                  "detail": str(exc)[:200]}))
            return _error(503, "model_unavailable", "prediction service temporarily unavailable")
        threshold = float(current["threshold"])
        flag = int(probability >= threshold)
        latency = round((time.perf_counter() - started) * 1000, 2)
        metrics.record(latency, probability, flag)
        log.info(json.dumps({"event": "prediction", "customer": _hash(body.customer_id),
                             "probability": round(probability, 4), "flag": flag,
                             "model_version": str(current.get("model_version")), "latency_ms": latency,
                             "overrides": sorted(body.overrides)}))
        return PredictResponse(customer_id=body.customer_id, churn_probability=round(probability, 6),
                               churn_flag=flag, threshold=threshold,
                               model_version=str(current.get("model_version")), latency_ms=latency)

    return app
