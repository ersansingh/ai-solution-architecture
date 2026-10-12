"""Pipeline step `Evaluate` (SageMaker Processing on the XGBoost 1.7-1 image) - also runs locally.

Inputs : <model>/model.tar.gz (or an extracted xgboost-model file), <validation>/validation.csv,
         <test>/test.csv  (encoded, label-first, no header)
Output : <output>/evaluation.json   metrics on TEST at a threshold chosen on VALIDATION + gate report

The approved-model AUC for the no-regression gate is read from the Model Registry when
--model-package-group is given (latest Approved package's model-quality statistics).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import tarfile
from typing import Optional
from urllib.parse import urlparse

import numpy as np
import xgboost as xgb

from churn.evaluate import compute_metrics, gate_report, select_threshold


def load_booster(model_dir: str) -> xgb.Booster:
    for archive in glob.glob(os.path.join(model_dir, "*.tar.gz")):
        with tarfile.open(archive) as tar:
            tar.extractall(model_dir)
    booster = xgb.Booster()
    booster.load_model(os.path.join(model_dir, "xgboost-model"))
    return booster


def load_split(path: str):
    files = sorted(glob.glob(os.path.join(path, "*.csv"))) if os.path.isdir(path) else [path]
    data = np.vstack([np.loadtxt(f, delimiter=",", ndmin=2) for f in files])
    return data[:, 1:], data[:, 0].astype(int)


def approved_auc(model_package_group: Optional[str]) -> Optional[float]:
    if not model_package_group:
        return None
    import boto3  # imported lazily: not needed for local runs

    sm, s3 = boto3.client("sagemaker"), boto3.client("s3")
    packages = sm.list_model_packages(
        ModelPackageGroupName=model_package_group, ModelApprovalStatus="Approved",
        SortBy="CreationTime", SortOrder="Descending", MaxResults=1,
    )["ModelPackageSummaryList"]
    if not packages:
        return None
    detail = sm.describe_model_package(ModelPackageName=packages[0]["ModelPackageArn"])
    uri = detail.get("ModelMetrics", {}).get("ModelQuality", {}).get("Statistics", {}).get("S3Uri")
    if not uri:
        return None
    parsed = urlparse(uri)
    body = s3.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))["Body"].read()
    return float(json.loads(body)["binary_classification_metrics"]["auc"]["value"])


def feature_importance(booster: xgb.Booster, top: int = 15) -> dict:
    """Gain importance by encoded feature name, plus 'dead' features never used in a split (Part 7)."""
    from churn.preprocessing import transformed_feature_names

    names = transformed_feature_names()
    gain = booster.get_score(importance_type="gain")
    by_name = {names[int(k[1:])]: round(v, 4) for k, v in gain.items() if k.startswith("f")}
    ranked = dict(sorted(by_name.items(), key=lambda kv: kv[1], reverse=True)[:top])
    return {"top_gain": ranked, "dead_features": [n for n in names if n not in by_name]}


def run(model_dir, validation, test, output_dir, gates, model_package_group=None) -> dict:
    booster = load_booster(model_dir)
    x_val, y_val = load_split(validation)
    x_test, y_test = load_split(test)
    threshold = select_threshold(y_val, booster.predict(xgb.DMatrix(x_val)), gates["threshold_target_recall"])
    metrics = compute_metrics(y_test, booster.predict(xgb.DMatrix(x_test)), threshold)
    metrics["gates"] = gate_report(metrics, gates, approved_auc(model_package_group))
    metrics["feature_importance"] = feature_importance(booster)
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "evaluation.json"), "w") as fh:
        json.dump(metrics, fh, indent=2)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="/opt/ml/processing/model")
    parser.add_argument("--validation", default="/opt/ml/processing/validation")
    parser.add_argument("--test", default="/opt/ml/processing/test")
    parser.add_argument("--output", default="/opt/ml/processing/evaluation")
    parser.add_argument("--auc", type=float, default=0.90)
    parser.add_argument("--precision", type=float, default=0.85)
    parser.add_argument("--recall", type=float, default=0.80)
    parser.add_argument("--accuracy", type=float, default=0.90)
    parser.add_argument("--max-auc-regression", type=float, default=0.01)
    parser.add_argument("--target-recall", type=float, default=0.82)
    parser.add_argument("--model-package-group", default="")
    args = parser.parse_args()
    gates = {
        "auc": args.auc, "precision": args.precision, "recall": args.recall, "accuracy": args.accuracy,
        "max_auc_regression": args.max_auc_regression, "threshold_target_recall": args.target_recall,
    }
    result = run(args.model, args.validation, args.test, args.output, gates, args.model_package_group or None)
    summary = {k: v["value"] for k, v in result["binary_classification_metrics"].items() if "value" in v}
    print(json.dumps({"metrics": summary, "threshold": result["threshold"], "gates": result["gates"]}, indent=2))


if __name__ == "__main__":
    main()
