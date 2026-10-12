"""M7 / AT-8: send drifted traffic straight to the endpoint so Model Monitor raises a violation.

Shifts monthly_charges +40% and satisfaction_score -2 (plan M7 task 6) on golden records, then
optionally starts an on-demand data-quality run of the schedule.

  python scripts/simulate_drift.py --endpoint customer-churn-prod --requests 2000 \
      --test-raw s3://<bucket>/training/<exec>/test_raw/test_raw.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from urllib.parse import urlparse

import boto3

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from churn import config  # noqa: E402


def drift(row: dict) -> dict:
    out = dict(row)
    if out.get("monthly_charges"):
        out["monthly_charges"] = f"{float(out['monthly_charges']) * 1.4:.2f}"
    if out.get("satisfaction_score"):
        out["satisfaction_score"] = str(max(1.0, float(out["satisfaction_score"]) - 2))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=config.project()["endpoints"]["prod"])
    parser.add_argument("--test-raw", required=True)
    parser.add_argument("--requests", type=int, default=2000)
    args = parser.parse_args()

    parsed = urlparse(args.test_raw)
    body = boto3.client("s3").get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))["Body"].read().decode()
    rows = list(csv.DictReader(io.StringIO(body)))
    columns = config.model_input_columns()
    runtime = boto3.client("sagemaker-runtime")
    for i in range(args.requests):
        row = drift(rows[i % len(rows)])
        runtime.invoke_endpoint(EndpointName=args.endpoint, ContentType="text/csv",
                                Body=",".join(row.get(c, "") for c in columns),
                                InferenceId=f"drift-{i}")
    print(f"sent {args.requests} drifted requests to {args.endpoint}; the next data-quality run "
          f"({args.endpoint}-data-quality) should report violations and fire churn-drift-* alarms")


if __name__ == "__main__":
    main()
