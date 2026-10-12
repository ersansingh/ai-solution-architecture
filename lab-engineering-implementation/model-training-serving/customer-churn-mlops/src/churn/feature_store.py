"""Feature Store helpers shared by the ingest job, the scoring snapshot and the tests.

The Feature Group itself (schema from config/features.yaml) is created by Terraform
(infra/terraform/modules/sagemaker). Here we only convert rows to records and back.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from churn import config


def feature_types() -> Dict[str, str]:
    """Feature name -> Feature Store type. Mirrors infra/terraform/modules/sagemaker/feature_group.tf."""
    feats = config.features()
    types = {feats["record_identifier"]: "String", feats["event_time"]: "String"}
    types.update({c: "Fractional" for c in config.numeric_columns()})
    types.update({c: "String" for c in config.categorical_columns()})
    return types


def to_record(row: Dict) -> List[Dict[str, str]]:
    """Feature Store PutRecord payload. Missing values are omitted (allowed by Feature Store)."""
    record = []
    for name, value in row.items():
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        record.append({"FeatureName": name, "ValueAsString": str(value)})
    return record


def from_record(record: List[Dict[str, str]]) -> Dict[str, Optional[object]]:
    """GetRecord response -> typed dict with every model-input column (missing -> None)."""
    values = {item["FeatureName"]: item["ValueAsString"] for item in record}
    numeric = set(config.numeric_columns())
    out: Dict[str, Optional[object]] = {}
    for column in config.model_input_columns():
        raw = values.get(column)
        out[column] = None if raw is None else (float(raw) if column in numeric else raw)
    return out
