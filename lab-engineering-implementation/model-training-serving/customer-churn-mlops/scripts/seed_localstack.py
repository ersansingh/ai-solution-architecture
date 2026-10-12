"""Seed LocalStack after `terraform apply` (envs/local) and local training.

  * raw data -> s3://<bucket>/raw-data/... (manifest last, like a real data drop)
  * features.csv -> DynamoDB online-feature table (Feature Store online-store stand-in)
  * serving config (threshold from evaluation.json) -> SSM, as publish_serving_config does on AWS

  python scripts/seed_localstack.py --work /work --bucket teleconnect-churn-local [--limit 20000]
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import boto3
import pandas as pd

from churn.feature_store import to_record


def upload_raw(s3, bucket: str, data_root: str) -> int:
    files = sorted(glob.glob(os.path.join(data_root, "raw-data", "**", "*.csv"), recursive=True))
    for path in files:
        s3.upload_file(path, bucket, os.path.relpath(path, data_root))
    for manifest in glob.glob(os.path.join(data_root, "raw-data", "ingest_date=*", "_MANIFEST.json")):
        s3.upload_file(manifest, bucket, os.path.relpath(manifest, data_root))
    return len(files)


def load_features(dynamodb, table: str, features_csv: str, limit: int) -> int:
    frame = pd.read_csv(features_csv, dtype={"customer_id": str}, nrows=limit)
    written = 0
    for start in range(0, len(frame), 25):
        batch = frame.iloc[start:start + 25].to_dict(orient="records")
        items = [{"PutRequest": {"Item": {"customer_id": {"S": row["customer_id"]},
                                          "record": {"S": json.dumps(to_record(row))}}}} for row in batch]
        response = dynamodb.batch_write_item(RequestItems={table: items})
        while response.get("UnprocessedItems"):
            response = dynamodb.batch_write_item(RequestItems=response["UnprocessedItems"])
        written += len(items)
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", default="/work")
    parser.add_argument("--bucket", default="teleconnect-churn-local")
    parser.add_argument("--table", default="teleconnect-online-features")
    parser.add_argument("--parameter", default="/teleconnect-churn/prod/serving-config")
    parser.add_argument("--limit", type=int, default=20_000)
    args = parser.parse_args()

    s3, dynamodb, ssm = boto3.client("s3"), boto3.client("dynamodb"), boto3.client("ssm")
    raw_files = upload_raw(s3, args.bucket, os.path.join(args.work, "data"))
    features = load_features(dynamodb, args.table, os.path.join(args.work, "processed", "features", "features.csv"),
                             args.limit)
    evaluation = json.load(open(os.path.join(args.work, "evaluation", "evaluation.json")))
    serving = {"endpoint_name": "local-model-server", "model_version": "local-1",
               "threshold": evaluation["threshold"],
               "auc": evaluation["binary_classification_metrics"]["auc"]["value"], "source": "seed"}
    ssm.put_parameter(Name=args.parameter, Value=json.dumps(serving), Type="String", Overwrite=True)
    print(json.dumps({"raw_files": raw_files, "online_features": features, "serving_config": serving}))


if __name__ == "__main__":
    main()
