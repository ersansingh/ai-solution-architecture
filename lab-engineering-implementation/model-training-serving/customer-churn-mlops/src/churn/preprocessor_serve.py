"""Inference handlers for container 1 of the PipelineModel (SageMaker scikit-learn 1.2-1 image).

Request : text/csv, one customer per line, columns in feature_contract.json["input_columns"] order
Response: text/csv, the encoded matrix (no label) that container 2 (built-in XGBoost) scores.
"""
from __future__ import annotations

import io
import json
import os

import joblib
import pandas as pd

CONTENT_TYPE = "text/csv"


def model_fn(model_dir):
    with open(os.path.join(model_dir, "feature_contract.json")) as fh:
        contract = json.load(fh)
    return {"preprocessor": joblib.load(os.path.join(model_dir, "preprocessor.joblib")), "contract": contract}


def input_fn(request_body, request_content_type):
    if request_content_type != CONTENT_TYPE:
        raise ValueError(f"unsupported content type {request_content_type}; send {CONTENT_TYPE}")
    if isinstance(request_body, bytes):
        request_body = request_body.decode("utf-8")
    return pd.read_csv(io.StringIO(request_body), header=None, na_values=[""], keep_default_na=False)


def predict_fn(input_data, model):
    columns = model["contract"]["input_columns"]
    if input_data.shape[1] != len(columns):
        raise ValueError(f"expected {len(columns)} columns, got {input_data.shape[1]}")
    input_data.columns = columns
    return model["preprocessor"].transform(input_data)


def output_fn(prediction, accept):
    buffer = io.StringIO()
    pd.DataFrame(prediction).to_csv(buffer, header=False, index=False, float_format="%.6g")
    return buffer.getvalue(), CONTENT_TYPE
