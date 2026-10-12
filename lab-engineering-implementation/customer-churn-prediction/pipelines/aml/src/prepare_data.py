"""Build the point-in-time training set from Feast and split it out-of-time.

1. Read matured 90-day labels (Gold ``churn_labels`` Delta table) for monthly
   snapshots in [snapshot_date - label_gap - history_months, snapshot_date - label_gap].
2. ``FeatureStore.get_historical_features`` point-in-time join (no leakage).
3. Group-aware, out-of-time split (no customer in more than one split):
   train/valid on in-time months, calib/test on the two latest matured months.
"""

from __future__ import annotations

import argparse
import hashlib
import os

import pandas as pd
from common import ID_COL, LABEL_COL, TIME_COL, write_split
from deltalake import DeltaTable
from feast import FeatureStore


def customer_bucket(cid: str) -> int:
    return int(hashlib.sha256(cid.encode()).hexdigest()[:8], 16) % 100


def assign_splits(df: pd.DataFrame) -> pd.DataFrame:
    months = sorted(df["snapshot_date"].unique())
    if len(months) < 4:
        raise ValueError(f"need >= 4 matured monthly snapshots, got {len(months)}")
    calib_month, test_month, valid_month = months[-2], months[-1], months[-3]
    bucket = df[ID_COL].map(customer_bucket)
    split = pd.Series("drop", index=df.index)
    split[(df["snapshot_date"] < valid_month) & (bucket < 60)] = "train"
    split[(df["snapshot_date"] == valid_month) & (bucket >= 60) & (bucket < 70)] = "valid"
    split[(df["snapshot_date"] == calib_month) & (bucket >= 70) & (bucket < 85)] = "calib"
    split[(df["snapshot_date"] == test_month) & (bucket >= 85)] = "test"
    return df.assign(split=split).query("split != 'drop'")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot-date", required=True)
    p.add_argument("--history-months", type=int, default=24)
    p.add_argument("--label-gap-days", type=int, default=90)
    p.add_argument("--labels", required=True, help="Gold churn_labels Delta table folder")
    p.add_argument("--feast-config", required=True, help="feature_store.yaml")
    p.add_argument("--feature-service", default="churn_model_v1")
    p.add_argument("--train-data", required=True)
    p.add_argument("--valid-data", required=True)
    p.add_argument("--calib-data", required=True)
    p.add_argument("--test-data", required=True)
    args = p.parse_args()

    end = pd.Timestamp(args.snapshot_date) - pd.Timedelta(days=args.label_gap_days)
    start = end - pd.DateOffset(months=args.history_months)
    labels = DeltaTable(args.labels).to_pandas()
    labels["snapshot_date"] = pd.to_datetime(labels["snapshot_date"])
    labels = labels[(labels["snapshot_date"] > start) & (labels["snapshot_date"] <= end)]
    entity_df = labels.rename(columns={"snapshot_date": TIME_COL})

    # Feast's Azure registry store and adlfs use DefaultAzureCredential; on an AML
    # cluster with a user-assigned identity, point it at that identity (id-aml).
    if os.environ.get("DEFAULT_IDENTITY_CLIENT_ID"):
        os.environ.setdefault("AZURE_CLIENT_ID", os.environ["DEFAULT_IDENTITY_CLIENT_ID"])
    store = FeatureStore(fs_yaml_file=args.feast_config)
    df = store.get_historical_features(
        entity_df=entity_df, features=store.get_feature_service(args.feature_service)
    ).to_df()
    df = df.rename(columns={TIME_COL: "snapshot_date"}).dropna(subset=[LABEL_COL])
    df = assign_splits(df)
    for name in ("train", "valid", "calib", "test"):
        part = df[df["split"] == name]
        print(f"{name}: rows={len(part)} positive_rate={part[LABEL_COL].mean():.4f}")
        write_split(part, getattr(args, f"{name}_data"))


if __name__ == "__main__":
    main()
