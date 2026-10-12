"""Cleaning, joining and the serialisable model preprocessor (plan G1-G4, section 6.1).

Order of operations (fixes Phase 3 leakage):
    merge sources -> clean/dedupe -> engineer features on raw values -> split
    -> fit ChurnPreprocessor on TRAIN only -> transform every split.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split

from churn import config

UNKNOWN = "Unknown"


def merge_sources(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Left-join every source onto customers on customer_id (churn optional for scoring data)."""
    key = config.features()["record_identifier"]
    merged = frames["customers"].drop_duplicates(subset=[key], keep="last")
    for name in ("billing", "usage", "support", "churn"):
        if name in frames:
            merged = merged.merge(frames[name].drop_duplicates(subset=[key], keep="last"), on=key, how="left")
    return merged


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact and key duplicates, coerce types, and encode the label to 0/1."""
    key = config.features()["record_identifier"]
    label = config.features()["label"]
    out = df.drop_duplicates().drop_duplicates(subset=[key], keep="last").copy()
    for column in config.features()["numeric"]:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    for column in config.categorical_columns():
        if column in out.columns:
            out[column] = out[column].where(out[column].notna(), None)
    if label in out.columns:
        mapped = out[label].map({"Yes": 1, "No": 0, 1: 1, 0: 0, "1": 1, "0": 0})
        out = out[mapped.notna()].copy()
        out[label] = mapped[mapped.notna()].astype(int)
    return out.reset_index(drop=True)


def split(
    df: pd.DataFrame, seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified 70/15/15 split."""
    label = config.features()["label"]
    train, temp = train_test_split(df, test_size=0.30, random_state=seed, stratify=df[label])
    validation, test = train_test_split(temp, test_size=0.50, random_state=seed, stratify=temp[label])
    return train.reset_index(drop=True), validation.reset_index(drop=True), test.reset_index(drop=True)


def transformed_feature_names(features_cfg: Optional[dict] = None) -> List[str]:
    """Deterministic column names of the encoded matrix (used by Clarify headers and SHAP plots)."""
    cfg = features_cfg or config.features()
    names = list(cfg["numeric"])
    names += [f"{c}_was_missing" for c in cfg["missing_indicators"]]
    for column, values in cfg["categorical"].items():
        names += [f"{column}={v}" for v in list(values) + [UNKNOWN]]
    return names


class ChurnPreprocessor(BaseEstimator, TransformerMixin):
    """Median impute + IQR cap + standardise numerics, explicit missing flags, fixed one-hot.

    Implemented without ColumnTransformer so that the fitted state is a handful of plain
    dicts: it unpickles across scikit-learn versions (training image vs serving image).
    """

    def __init__(self, iqr_multiplier: float = 1.5):
        self.iqr_multiplier = iqr_multiplier

    def fit(self, X: pd.DataFrame, y=None):
        cfg = config.features()
        self.numeric_ = list(cfg["numeric"])
        self.indicators_ = list(cfg["missing_indicators"])
        self.categories_ = {c: [str(v) for v in vals] + [UNKNOWN] for c, vals in cfg["categorical"].items()}
        numeric = X[self.numeric_].astype(float)
        self.medians_ = numeric.median().fillna(0.0).to_dict()
        q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
        iqr = q3 - q1
        self.lower_ = (q1 - self.iqr_multiplier * iqr).to_dict()
        self.upper_ = (q3 + self.iqr_multiplier * iqr).to_dict()
        capped = self._impute_and_cap(numeric)
        self.means_ = capped.mean().to_dict()
        self.stds_ = capped.std(ddof=0).replace(0, 1.0).fillna(1.0).to_dict()
        self.feature_names_ = transformed_feature_names(cfg)
        return self

    def _impute_and_cap(self, numeric: pd.DataFrame) -> pd.DataFrame:
        filled = numeric.fillna(self.medians_)
        return filled.clip(lower=pd.Series(self.lower_), upper=pd.Series(self.upper_), axis=1)

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        numeric = X[self.numeric_].apply(pd.to_numeric, errors="coerce").astype(float)
        scaled = (self._impute_and_cap(numeric) - pd.Series(self.means_)) / pd.Series(self.stds_)
        blocks = [scaled[self.numeric_].to_numpy()]
        blocks.append(numeric[self.indicators_].isna().astype(float).to_numpy())
        for column, vocabulary in self.categories_.items():
            values = X[column].astype(object).where(X[column].notna(), UNKNOWN).astype(str)
            values = values.where(values.isin(vocabulary), UNKNOWN)
            one_hot = np.zeros((len(X), len(vocabulary)))
            index = {v: i for i, v in enumerate(vocabulary)}
            one_hot[np.arange(len(X)), values.map(index).to_numpy()] = 1.0
            blocks.append(one_hot)
        return np.hstack(blocks)

    def get_feature_names_out(self, input_features=None) -> np.ndarray:
        return np.array(self.feature_names_)


def label_first(matrix: np.ndarray, labels: pd.Series) -> np.ndarray:
    """Built-in XGBoost / Linear Learner CSV format: label in column 0, no header (plan G4)."""
    return np.column_stack([labels.to_numpy().astype(float), matrix])
