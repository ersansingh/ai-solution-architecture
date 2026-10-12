"""Pipeline step `IngestFeatures`: write features.csv into the Feature Group (online + offline).

PutRecord is used (via a thread pool) so the online store is populated for churn-api look-ups;
the offline store is filled asynchronously by SageMaker from the same records.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor

import boto3
import pandas as pd
from botocore.config import Config

from churn.feature_store import to_record


def ingest(features_dir: str, feature_group: str, workers: int, region: str) -> dict:
    client = boto3.client("sagemaker-featurestore-runtime", region_name=region,
                          config=Config(retries={"max_attempts": 10, "mode": "adaptive"},
                                        max_pool_connections=workers))
    files = sorted(glob.glob(os.path.join(features_dir, "*.csv")))
    sent, failed = 0, []

    def put(row: dict):
        client.put_record(FeatureGroupName=feature_group, Record=to_record(row))

    for path in files:
        for chunk in pd.read_csv(path, chunksize=50_000, dtype={"customer_id": str}):
            rows = chunk.to_dict(orient="records")
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for row, error in zip(rows, pool.map(_safe(put), rows)):
                    if error:
                        failed.append({"customer_id": row["customer_id"], "error": error})
            sent += len(rows)
    if failed and len(failed) > 0.001 * max(sent, 1):
        raise RuntimeError(f"{len(failed)} of {sent} records failed: {failed[:5]}")
    return {"records": sent, "failed": len(failed)}


def _safe(fn):
    def wrapper(row):
        try:
            fn(row)
            return None
        except Exception as exc:  # noqa: BLE001 - collected and reported in bulk
            return str(exc)
    return wrapper


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", default="/opt/ml/processing/input/features")
    parser.add_argument("--feature-group", required=True)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION")))
    args = parser.parse_args()
    print(json.dumps(ingest(args.features, args.feature_group, args.workers, args.region)))


if __name__ == "__main__":
    main()
