"""Local stand-in for the SageMaker PipelineModel endpoint (same container contract).

GET /ping -> 200 when the model is loaded; POST /invocations text/csv rows -> one probability per line.
Loads <MODEL_DIR>/preprocessor.joblib, feature_contract.json and xgboost-model produced by
`python -m churn.jobs.local_train`, and reuses the exact serving handlers of container 1.
"""
from __future__ import annotations

import os

import xgboost as xgb
from fastapi import FastAPI, Request, Response

from churn import preprocessor_serve

MODEL_DIR = os.environ.get("MODEL_DIR", "/opt/ml/model")


def create_app(model_dir: str = MODEL_DIR) -> FastAPI:
    app = FastAPI(title="churn model server (local)")
    preprocessor = preprocessor_serve.model_fn(model_dir)
    booster = xgb.Booster()
    booster.load_model(os.path.join(model_dir, "xgboost-model"))

    @app.get("/ping")
    def ping():
        return Response(status_code=200)

    @app.post("/invocations")
    async def invocations(request: Request):
        body = await request.body()
        try:
            frame = preprocessor_serve.input_fn(body, request.headers.get("content-type", "text/csv").split(";")[0])
            encoded = preprocessor_serve.predict_fn(frame, preprocessor)
        except ValueError as exc:
            return Response(content=str(exc), status_code=400)
        probabilities = booster.predict(xgb.DMatrix(encoded))
        return Response(content="\n".join(f"{p:.6f}" for p in probabilities) + "\n", media_type="text/csv")

    return app
