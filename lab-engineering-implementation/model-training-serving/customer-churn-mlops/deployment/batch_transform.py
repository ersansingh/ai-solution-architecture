"""M6: score the full customer base (5M) with Batch Transform (plan section 6.4).

1. Athena UNLOAD of the latest Feature Store record per customer -> predictions/input/<run_date>/
   (many files, so Batch Transform can spread them over instances).
2. Batch Transform with the latest Approved PipelineModel package.
3. Post-process: apply the serving threshold -> predictions/output/<run_date>/scored/.

  python deployment/batch_transform.py --run-date 2026-10-10 [--model-package-arn ARN] [--instances 4]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from datetime import date
from pathlib import Path

import boto3
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from churn import config  # noqa: E402


def latest_approved_package(sm, group: str) -> str:
    packages = sm.list_model_packages(ModelPackageGroupName=group, ModelApprovalStatus="Approved",
                                      SortBy="CreationTime", SortOrder="Descending", MaxResults=1)
    if not packages["ModelPackageSummaryList"]:
        raise SystemExit(f"no Approved package in {group}")
    return packages["ModelPackageSummaryList"][0]["ModelPackageArn"]


def snapshot_query(database: str, table: str) -> str:
    key = config.features()["record_identifier"]
    numeric = set(config.numeric_columns())
    # Empty string (not \\N) for nulls so the CSV parser in the preprocessor sees missing values.
    cols = ",".join(
        f"coalesce(cast({c} as varchar), '')" if c in numeric else f"coalesce({c}, '')"
        for c in config.model_input_columns()
    )
    return f"""
SELECT {key}, {cols}
FROM (
  SELECT *, row_number() OVER (PARTITION BY {key} ORDER BY event_time DESC, api_invocation_time DESC) AS rn
  FROM "{database}"."{table}"
  WHERE NOT is_deleted
)
WHERE rn = 1"""


def build_snapshot(run_date: str, workgroup: str) -> str:
    cfg = config.project()
    sm, athena = boto3.client("sagemaker"), boto3.client("athena")
    catalog = sm.describe_feature_group(FeatureGroupName=cfg["feature_group_name"])[
        "OfflineStoreConfig"]["DataCatalogConfig"]
    target = config.s3_uri("predictions", "input", run_date) + "/"
    query = (f"UNLOAD ({snapshot_query(catalog['Database'], catalog['TableName'])}) TO '{target}' "
             "WITH (format = 'TEXTFILE', field_delimiter = ',', compression = 'NONE')")
    qid = athena.start_query_execution(QueryString=query, WorkGroup=workgroup)["QueryExecutionId"]
    while True:
        state = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        if state["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(5)
    if state["State"] != "SUCCEEDED":
        raise SystemExit(f"snapshot failed: {state}")
    return target


def run_transform(input_uri: str, run_date: str, package_arn: str, instances: int) -> str:
    import sagemaker
    from sagemaker import ModelPackage

    cfg = config.project()
    session = sagemaker.Session()
    model = ModelPackage(role=cfg["sagemaker_role_arn"], model_package_arn=package_arn, sagemaker_session=session)
    output = config.s3_uri("predictions", "output", run_date, "raw")
    transformer = model.transformer(
        instance_count=instances, instance_type=cfg["instance_types"]["batch"], output_path=output,
        strategy="MultiRecord", assemble_with="Line", accept="text/csv",
        max_payload=int(cfg["batch"]["max_payload_mb"]),
        max_concurrent_transforms=int(cfg["batch"]["max_concurrent_transforms"]),
    )
    started = time.time()
    transformer.transform(
        data=input_uri, content_type="text/csv", split_type="Line",
        input_filter="$[1:]",        # drop customer_id before the model
        join_source="Input",         # ... but keep it in the output
        output_filter="$[0,-1]",     # customer_id, churn_probability
        wait=True, logs=False,
    )
    print(json.dumps({"transform_job": transformer.latest_transform_job.name,
                      "minutes": round((time.time() - started) / 60, 1)}))
    return output


def post_process(raw_output: str, run_date: str) -> dict:
    """Apply the serving threshold; write one scored CSV per Batch Transform output file."""
    cfg = config.project()
    s3, ssm = boto3.client("s3"), boto3.client("ssm")
    serving = json.loads(ssm.get_parameter(Name=cfg["serving_config_parameter"].format(stage="prod"))
                         ["Parameter"]["Value"])
    bucket = cfg["bucket"]
    prefix = raw_output.split(f"s3://{bucket}/", 1)[1].rstrip("/") + "/"
    rows = churners = 0
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            body = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read()
            frame = pd.read_csv(io.BytesIO(body), header=None, names=["customer_id", "churn_probability"])
            frame["churn_flag"] = (frame["churn_probability"] >= serving["threshold"]).astype(int)
            frame["model_version"] = serving["model_version"]
            frame["scored_date"] = run_date
            rows += len(frame)
            churners += int(frame["churn_flag"].sum())
            key = f"{cfg['prefixes']['predictions']}/output/{run_date}/scored/{Path(obj['Key']).name}.csv"
            s3.put_object(Bucket=bucket, Key=key, Body=frame.to_csv(index=False).encode())
    return {"rows": rows, "predicted_churners": churners, "threshold": serving["threshold"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", default=date.today().isoformat())
    parser.add_argument("--model-package-arn", default="")
    parser.add_argument("--instances", type=int, default=int(config.project()["batch"]["instance_count"]))
    parser.add_argument("--athena-workgroup", default="teleconnect-churn")
    parser.add_argument("--input-uri", default="", help="skip the snapshot and score this prefix")
    args = parser.parse_args()

    sm = boto3.client("sagemaker")
    package = args.model_package_arn or latest_approved_package(sm, config.project()["model_package_group"])
    input_uri = args.input_uri or build_snapshot(args.run_date, args.athena_workgroup)
    raw = run_transform(input_uri, args.run_date, package, args.instances)
    print(json.dumps(post_process(raw, args.run_date)))


if __name__ == "__main__":
    main()
