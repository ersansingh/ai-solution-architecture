"""Random Forest challenger - SageMaker scikit-learn script mode entry point (plan M3).

Channels: train, validation (encoded, label-first, no header). Prints metrics in a form the
estimator's metric_definitions scrape into SageMaker Experiments.
"""
from __future__ import annotations

import argparse
import glob
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, roc_auc_score


def load(channel_dir: str):
    data = np.vstack([np.loadtxt(f, delimiter=",", ndmin=2) for f in sorted(glob.glob(f"{channel_dir}/*.csv"))])
    return data[:, 1:], data[:, 0].astype(int)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=16)
    parser.add_argument("--min-samples-leaf", type=int, default=20)
    parser.add_argument("--model-dir", default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train", default=os.environ.get("SM_CHANNEL_TRAIN"))
    parser.add_argument("--validation", default=os.environ.get("SM_CHANNEL_VALIDATION"))
    args = parser.parse_args()

    x_train, y_train = load(args.train)
    model = RandomForestClassifier(
        n_estimators=args.n_estimators, max_depth=args.max_depth, min_samples_leaf=args.min_samples_leaf,
        class_weight="balanced", n_jobs=-1, random_state=42,
    ).fit(x_train, y_train)

    x_val, y_val = load(args.validation)
    prob = model.predict_proba(x_val)[:, 1]
    pred = (prob >= 0.5).astype(int)
    print(f"validation:auc={roc_auc_score(y_val, prob):.5f};")
    print(f"validation:precision={precision_score(y_val, pred, zero_division=0):.5f};")
    print(f"validation:recall={recall_score(y_val, pred):.5f};")
    joblib.dump(model, os.path.join(args.model_dir, "model.joblib"))


def model_fn(model_dir):
    return joblib.load(os.path.join(model_dir, "model.joblib"))


if __name__ == "__main__":
    main()
