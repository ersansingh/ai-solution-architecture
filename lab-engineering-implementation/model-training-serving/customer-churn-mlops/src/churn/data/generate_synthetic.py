"""Synthetic TeleConnect data at production scale (plan D1/D2).

Scales the training-samples schema to N customers with:
  * ~18% churn driven by a learnable signal (contract, satisfaction, complaints, tenure,
    payment delay, usage decline) plus noise,
  * 3-5% nulls in selected columns and ~0.5% duplicate rows per source,
  * the two extra source columns needed for the required features:
    data_usage_gb_prev_3m (usage growth) and avg_days_past_due (payment delay).

Output layout mirrors the S3 data lake:
  <out>/raw-data/<source>/ingest_date=<date>/<source>.csv
  <out>/raw-data/ingest_date=<date>/_MANIFEST.json   (written last; retraining trigger)

Usage:
  python -m churn.data.generate_synthetic --rows 2500000 --out ./data --ingest-date 2026-10-01
  python -m churn.data.generate_synthetic --rows 5000000 --out ./data --scoring   # no churn file
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
from typing import Dict

import numpy as np
import pandas as pd

from churn import config

TARGET_CHURN_RATE = 0.18
NULL_RATE = 0.04
DUPLICATE_RATE = 0.005
CHUNK_SIZE = 500_000
# Scales the latent logit. 2.5 with noise 0.5 gives AUC ~0.98, so the KPI gates are reachable
# but not trivial; lower it to rehearse a failing quality gate.
SIGNAL_STRENGTH = 2.5
NULLABLE = {
    "billing": ["monthly_charges", "total_charges", "payment_method", "contract_type"],
    "usage": ["data_usage_gb", "voice_minutes"],
    "support": ["satisfaction_score"],
    "customers": ["region", "customer_segment"],
}


def _choice(rng, values, probs, n):
    return rng.choice(np.array(values, dtype=object), size=n, p=probs)


def _population(rng: np.random.Generator, n: int, first_id: int) -> pd.DataFrame:
    df = pd.DataFrame({"customer_id": np.arange(first_id, first_id + n)})
    df["age"] = rng.integers(18, 76, n)
    df["gender"] = _choice(rng, ["Female", "Male"], [0.45, 0.55], n)
    df["region"] = _choice(rng, ["East", "North", "South", "West"], [0.23, 0.30, 0.19, 0.28], n)
    df["customer_segment"] = _choice(rng, ["Business", "Consumer", "Enterprise"], [0.30, 0.40, 0.30], n)
    df["tenure_months"] = rng.integers(1, 73, n)

    df["contract_type"] = _choice(rng, ["Month-to-Month", "One Year", "Two Year"], [0.54, 0.25, 0.21], n)
    df["payment_method"] = _choice(rng, ["Bank Transfer", "Credit Card", "Debit Card", "UPI"],
                                   [0.25, 0.30, 0.25, 0.20], n)
    df["internet_package"] = _choice(rng, ["5G", "Cable", "DSL", "Fiber"], [0.25, 0.23, 0.27, 0.25], n)
    package_base = df["internet_package"].map({"DSL": 40.0, "Cable": 60.0, "Fiber": 85.0, "5G": 95.0})
    df["monthly_charges"] = np.round(np.clip(package_base + rng.normal(0, 25, n), 20, 150), 2)
    df["total_charges"] = np.round(df["monthly_charges"] * df["tenure_months"] * rng.uniform(0.9, 1.1, n), 2)
    df["avg_days_past_due"] = np.round(rng.gamma(1.2, 6.0, n), 1)
    df["outstanding_balance"] = np.round(np.clip(df["avg_days_past_due"] * rng.uniform(0.5, 3.0, n), 0, 400), 2)

    df["voice_minutes"] = rng.integers(80, 2500, n)
    df["data_usage_gb_prev_3m"] = np.round(rng.uniform(10, 800, n), 1)
    df["data_usage_gb"] = np.round(np.clip(df["data_usage_gb_prev_3m"] * rng.lognormal(0, 0.25, n), 1, 1200), 1)
    df["roaming_minutes"] = rng.integers(0, 301, n)
    df["streaming_service"] = _choice(rng, ["No", "Yes"], [0.48, 0.52], n)

    df["satisfaction_score"] = np.clip(np.round(rng.normal(6.2, 2.3, n)), 1, 10).astype(int)
    unhappy = (10 - df["satisfaction_score"]) / 9
    df["complaint_count"] = np.clip(rng.poisson(0.4 + 3.0 * unhappy), 0, 5)
    df["support_calls"] = np.clip(rng.poisson(2 + 6 * unhappy), 0, 12)
    df["tickets"] = np.clip(df["complaint_count"] + rng.poisson(2, n), 0, 10)
    df["avg_resolution_hours"] = rng.integers(2, 73, n)
    return df


def churn_logit(df: pd.DataFrame) -> np.ndarray:
    """Ground-truth churn log-odds (before intercept and noise)."""
    usage_growth = (df["data_usage_gb"] - df["data_usage_gb_prev_3m"]) / (df["data_usage_gb_prev_3m"] + 1)
    contract = df["contract_type"].map({"Month-to-Month": 1.8, "One Year": -0.6, "Two Year": -2.2})
    return SIGNAL_STRENGTH * (
        contract.to_numpy()
        - 0.75 * (df["satisfaction_score"].to_numpy() - 5.5)
        + 0.55 * df["complaint_count"].to_numpy()
        - 0.05 * df["tenure_months"].to_numpy()
        + 0.07 * df["avg_days_past_due"].to_numpy()
        - 2.5 * np.clip(usage_growth.to_numpy(), -1, 1)
        + 0.12 * df["support_calls"].to_numpy()
        + 0.01 * (df["monthly_charges"].to_numpy() - 75)
    )


def calibrate_intercept(rng: np.random.Generator, noise_sd: float, rate: float = TARGET_CHURN_RATE) -> float:
    """Bisection on a large sample so P(churn) == rate."""
    sample = _population(rng, 200_000, 0)
    logit = churn_logit(sample) + rng.normal(0, noise_sd, len(sample))
    lo, hi = -20.0, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if (1 / (1 + np.exp(-(logit + mid)))).mean() > rate:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def _inject_quality_issues(rng, frame: pd.DataFrame, source: str) -> pd.DataFrame:
    frame = frame.copy()
    for column in NULLABLE.get(source, []):
        mask = rng.random(len(frame)) < NULL_RATE
        frame[column] = frame[column].astype(object)
        frame.loc[mask, column] = None
    duplicates = frame.sample(frac=DUPLICATE_RATE, random_state=int(rng.integers(1 << 31)))
    return pd.concat([frame, duplicates]).sample(frac=1.0, random_state=int(rng.integers(1 << 31)))


def generate(rows: int, out_dir: str, ingest_date: str, scoring: bool = False, seed: int = 7,
             first_id: int = 100_000, noise_sd: float = 0.5) -> Dict[str, str]:
    rng = np.random.default_rng(seed)
    intercept = calibrate_intercept(np.random.default_rng(seed + 1), noise_sd)
    sources = dict(config.features()["sources"])
    if scoring:
        sources.pop("churn")
    paths = {}
    for name in sources:
        directory = os.path.join(out_dir, "raw-data", name, f"ingest_date={ingest_date}")
        os.makedirs(directory, exist_ok=True)
        paths[name] = os.path.join(directory, f"{name}.csv")
        if os.path.exists(paths[name]):
            os.remove(paths[name])

    churned, written = 0, 0
    for start in range(0, rows, CHUNK_SIZE):
        n = min(CHUNK_SIZE, rows - start)
        df = _population(rng, n, first_id + start)
        p = 1 / (1 + np.exp(-(churn_logit(df) + intercept + rng.normal(0, noise_sd, n))))
        df["churn"] = np.where(rng.random(n) < p, "Yes", "No")
        churned += int((df["churn"] == "Yes").sum())
        written += n
        for name, columns in sources.items():
            chunk = _inject_quality_issues(rng, df[columns], name)
            chunk.to_csv(paths[name], mode="a", header=start == 0, index=False)

    manifest = {
        "ingest_date": ingest_date,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rows": written,
        "scoring": scoring,
        "churn_rate": None if scoring else round(churned / written, 4),
        "files": {name: os.path.relpath(path, out_dir) for name, path in paths.items()},
    }
    manifest_dir = os.path.join(out_dir, "raw-data", f"ingest_date={ingest_date}")
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, "_MANIFEST.json")
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    paths["manifest"] = manifest_path
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", type=int, default=2_500_000)
    parser.add_argument("--out", default="./data")
    parser.add_argument("--ingest-date", default=date.today().isoformat())
    parser.add_argument("--scoring", action="store_true", help="scoring population: no churn labels")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--first-id", type=int, default=100_000)
    args = parser.parse_args()
    paths = generate(args.rows, args.out, args.ingest_date, args.scoring, args.seed, args.first_id)
    print(json.dumps(paths, indent=2))


if __name__ == "__main__":
    main()
