"""Ground-truth merge for Model Quality monitoring (plan G12).

churn-api invokes the endpoint with InferenceId="<customer_id>:<YYYYMMDD>". When the churn labels
for that cohort land (raw-data/churn/ingest_date=...), this job writes one ground-truth line per
captured inference under monitoring/ground-truth/YYYY/MM/DD/HH/, mirroring the capture hour.

  python deployment/ground_truth.py --capture-date 2026-07-12 \
      --labels s3://<bucket>/raw-data/churn/ingest_date=2026-10-10/churn.csv
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlparse

import boto3
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from churn import config  # noqa: E402


def ground_truth_lines(capture_lines: Iterable[str], labels: Dict[str, int]) -> List[str]:
    out = []
    for line in capture_lines:
        if not line.strip():
            continue
        event = json.loads(line)
        inference_id = event.get("eventMetadata", {}).get("inferenceId")
        if not inference_id:
            continue
        customer_id = inference_id.split(":", 1)[0]
        if customer_id not in labels:
            continue
        out.append(json.dumps({
            "groundTruthData": {"data": str(labels[customer_id]), "encoding": "CSV"},
            "eventMetadata": {"eventId": inference_id},
            "eventVersion": "0",
        }))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-date", required=True, help="YYYY-MM-DD of the captured inferences")
    parser.add_argument("--labels", required=True, help="s3:// URI of churn.csv (customer_id,churn)")
    parser.add_argument("--endpoint", default=config.project()["endpoints"]["prod"])
    args = parser.parse_args()

    cfg = config.project()
    s3 = boto3.client("s3")
    parsed = urlparse(args.labels)
    labels_df = pd.read_csv(io.BytesIO(s3.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))["Body"].read()),
                            dtype={"customer_id": str})
    labels = dict(zip(labels_df["customer_id"], labels_df["churn"].map({"Yes": 1, "No": 0, 1: 1, 0: 0})))

    y, m, d = args.capture_date.split("-")
    prefix = f"{cfg['prefixes']['monitoring']}/data-capture/{args.endpoint}/{cfg['variant_name']}/{y}/{m}/{d}/"
    by_hour = defaultdict(list)
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=cfg["bucket"], Prefix=prefix):
        for obj in page.get("Contents", []):
            hour = obj["Key"][len(prefix):].split("/", 1)[0]
            body = s3.get_object(Bucket=cfg["bucket"], Key=obj["Key"])["Body"].read().decode()
            by_hour[hour].extend(ground_truth_lines(body.splitlines(), labels))
    written = 0
    for hour, lines in by_hour.items():
        key = f"{cfg['prefixes']['monitoring']}/ground-truth/{y}/{m}/{d}/{hour}/labels.jsonl"
        s3.put_object(Bucket=cfg["bucket"], Key=key, Body="\n".join(lines).encode())
        written += len(lines)
    print(json.dumps({"capture_date": args.capture_date, "ground_truth_records": written}))


if __name__ == "__main__":
    main()
