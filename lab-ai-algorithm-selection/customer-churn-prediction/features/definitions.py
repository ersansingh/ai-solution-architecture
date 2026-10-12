"""Feast definitions for the churn platform (applied by CI: `feast apply`).

Entity ``customer`` (join key ``pseudo_customer_id``, keyed-HMAC pseudonym) and
three feature views:

* ``customer_features``: daily Gold features (data_contracts/gold_customer_features.json);
  the model's training/serving vector (feature service ``churn_model_v1``, used
  by pipelines/aml prepare_data; calibrate.py writes ``customer_features:<f>``
  refs into calibrator.json for the transformer's rescoring path).
* ``customer_streaming``: windowed streaming features pushed by Stream
  Analytics / Structured Streaming (system-design.md 6.3), incl.
  ``last_material_event_ts`` that decides precomputed vs rescoring.
* ``churn_score``: daily batch scores pushed after scoring (6.1 step 7), read by
  the transformer's precomputed path.

Offline sources are Parquet snapshots on the lake ``feast-offline`` filesystem.
Fairness/audit columns (country, region, age_band, gender) are deliberately not
features; they travel with the Gold labels (system-design.md 7.6).
"""

import os
from datetime import timedelta

from feast import Entity, FeatureService, FeatureView, Field, FileSource, PushSource
from feast.data_format import ParquetFormat
from feast.types import Float64, Int64, String, UnixTimestamp
from feast.value_type import ValueType

LAKE = os.environ.get("LAKE_STORAGE_ACCOUNT")
if not LAKE:
    raise RuntimeError("set LAKE_STORAGE_ACCOUNT (terraform output lake_storage_account_name)")
OFFLINE_ROOT = f"abfss://feast-offline@{LAKE}.dfs.core.windows.net/offline"

customer = Entity(
    name="customer",
    join_keys=["pseudo_customer_id"],
    value_type=ValueType.STRING,
    description="Customer, keyed-HMAC pseudonymous id (never a raw identifier)",
)

# --- daily Gold features ----------------------------------------------------
customer_features_source = FileSource(
    name="gold_customer_features",
    path=f"{OFFLINE_ROOT}/customer_features/",
    file_format=ParquetFormat(),
    timestamp_field="feature_event_ts",
    description="Gold point-in-time feature snapshot exported by Databricks",
)

customer_features = FeatureView(
    name="customer_features",
    entities=[customer],
    ttl=timedelta(days=7),
    schema=[
        Field(name="tenure_months", dtype=Int64),
        Field(name="monthly_charges", dtype=Float64),
        Field(name="data_usage_30d_delta_pct", dtype=Float64),
        Field(name="support_tickets_90d", dtype=Int64),
        Field(name="failed_payments_90d", dtype=Int64),
        Field(name="contract_months_remaining", dtype=Int64),
        Field(name="app_sessions_30d", dtype=Int64),
    ],
    source=customer_features_source,
    online=True,
    tags={"owner": "churn-data-engineering", "contract": "gold_customer_features@1.0.0"},
)

# --- streaming features (push) ---------------------------------------------
customer_streaming_push = PushSource(
    name="customer_streaming_push",
    batch_source=FileSource(
        name="customer_streaming_offline",
        path=f"{OFFLINE_ROOT}/customer_streaming/",
        file_format=ParquetFormat(),
        timestamp_field="event_timestamp",
    ),
)

customer_streaming = FeatureView(
    name="customer_streaming",
    entities=[customer],
    ttl=timedelta(days=2),
    schema=[
        Field(name="tickets_24h", dtype=Int64),
        Field(name="failed_payments_7d", dtype=Int64),
        Field(name="app_sessions_7d_delta", dtype=Float64),
        Field(name="last_material_event_ts", dtype=UnixTimestamp),
    ],
    source=customer_streaming_push,
    online=True,
    tags={"owner": "churn-data-engineering", "slo": "freshness<5m"},
)

# --- precomputed batch scores (push) ---------------------------------------
churn_score_push = PushSource(
    name="churn_score_push",
    batch_source=FileSource(
        name="churn_scores_offline",
        path=f"{OFFLINE_ROOT}/churn_scores/",
        file_format=ParquetFormat(),
        timestamp_field="event_timestamp",
    ),
)

churn_score = FeatureView(
    name="churn_score",
    entities=[customer],
    ttl=timedelta(days=3),
    schema=[
        Field(name="probability", dtype=Float64),
        Field(name="tier", dtype=String),
        Field(name="reason_codes", dtype=String),  # comma-separated, <= 5 codes
        Field(name="model_version", dtype=String),
        Field(name="score_ts", dtype=UnixTimestamp),
    ],
    source=churn_score_push,
    online=True,
    tags={"owner": "churn-ml", "writer": "aml-batch-scoring"},
)

# --- feature services -------------------------------------------------------
churn_model_v1 = FeatureService(
    name="churn_model_v1",
    features=[customer_features],
    description="Model input vector (training: prepare_data; serving: rescoring path)",
)

churn_online_v1 = FeatureService(
    name="churn_online_v1",
    features=[churn_score, customer_streaming[["last_material_event_ts"]]],
    description="Transformer precomputed path (score + freshness decision)",
)
