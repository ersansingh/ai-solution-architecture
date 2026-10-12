"""Pipeline step `Preprocess` (SageMaker Processing, scikit-learn 1.2-1) - also runs locally.

Inputs : <input>/raw-data/<source>/ingest_date=*/  (newest partition per source is used)
Outputs: <output>/
   train/train.csv              encoded, label-first, no header   (XGBoost / Linear Learner)
   validation/validation.csv    encoded, label-first, no header
   test/test.csv                encoded, label-first, no header   (evaluation)
   test_raw/test_raw.csv        customer_id + model-input columns + label, header (golden records)
   clarify/clarify.csv          5k-row encoded sample, label-first, no header (Clarify SHAP / bias;
                                headers come from churn.preprocessing.transformed_feature_names)
   baseline/baseline.csv        raw model-input columns, no header (Model Monitor data quality)
   features/features.csv        customer_id, event_time + model-input columns (Feature Store ingest)
   model/preprocessor.joblib    fitted ChurnPreprocessor
   model/feature_contract.json  input column order + encoded names
   model/model.tar.gz           the two files above, packaged for SKLearnModel
   report/data_quality.json     row counts, null rates, duplicates removed, churn rate per split
"""
from __future__ import annotations

import argparse
import json
import os
import tarfile
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from churn import config, io
from churn.feature_engineering import add_engineered_features
from churn.preprocessing import ChurnPreprocessor, clean, label_first, merge_sources, split

CLARIFY_SAMPLE = 5000


def _write(df_or_array, path: str, header: bool = True) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(df_or_array, np.ndarray):
        np.savetxt(path, df_or_array, delimiter=",", fmt="%.6g")
    else:
        df_or_array.to_csv(path, index=False, header=header)


def run(input_root: str, output_root: str, seed: int = 42) -> dict:
    feats = config.features()
    key, label = feats["record_identifier"], feats["label"]
    columns = config.model_input_columns()

    frames = io.load_raw(os.path.join(input_root, "raw-data"))
    duplicate_rows = {name: int(len(f) - f[key].nunique()) for name, f in frames.items()}
    raw = merge_sources(frames)
    data = add_engineered_features(clean(raw))
    labelled = data[data[label].notna()] if label in data.columns else data.iloc[0:0]

    train, validation, test = split(labelled, seed=seed)
    pre = ChurnPreprocessor().fit(train[columns])
    names = list(pre.get_feature_names_out())

    for name, frame in (("train", train), ("validation", validation), ("test", test)):
        _write(label_first(pre.transform(frame[columns]), frame[label]), f"{output_root}/{name}/{name}.csv")

    _write(test[[key] + columns + [label]], f"{output_root}/test_raw/test_raw.csv")
    sample = test.sample(n=min(CLARIFY_SAMPLE, len(test)), random_state=seed)
    clarify = pd.DataFrame(label_first(pre.transform(sample[columns]), sample[label]), columns=[label] + names)
    _write(clarify, f"{output_root}/clarify/clarify.csv", header=False)
    _write(train[columns], f"{output_root}/baseline/baseline.csv", header=False)

    event_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    feature_rows = data[[key] + columns].copy()
    feature_rows.insert(1, feats["event_time"], event_time)
    _write(feature_rows, f"{output_root}/features/features.csv")

    os.makedirs(f"{output_root}/model", exist_ok=True)
    joblib.dump(pre, f"{output_root}/model/preprocessor.joblib")
    with open(f"{output_root}/model/feature_contract.json", "w") as fh:
        json.dump({"input_columns": columns, "encoded_columns": names, "label": label}, fh, indent=2)
    # SKLearnModel (first container of the PipelineModel) needs a model.tar.gz.
    with tarfile.open(f"{output_root}/model/model.tar.gz", "w:gz") as tar:
        for name in ("preprocessor.joblib", "feature_contract.json"):
            tar.add(f"{output_root}/model/{name}", arcname=name)

    report = {
        "rows_clean": len(data),
        "duplicate_rows_removed": duplicate_rows,
        "null_rate_before_imputation": {c: round(float(data[c].isna().mean()), 4) for c in columns},
        "churn_rate": {
            n: round(float(f[label].mean()), 4)
            for n, f in (("train", train), ("validation", validation), ("test", test))
        },
        "split_rows": {"train": len(train), "validation": len(validation), "test": len(test)},
        "encoded_feature_count": len(names),
    }
    os.makedirs(f"{output_root}/report", exist_ok=True)
    with open(f"{output_root}/report/data_quality.json", "w") as fh:
        json.dump(report, fh, indent=2)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="/opt/ml/processing/input")
    parser.add_argument("--output", default="/opt/ml/processing/output")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output, args.seed), indent=2))


if __name__ == "__main__":
    main()
