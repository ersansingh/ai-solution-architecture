import pickle

import numpy as np
import pandas as pd

from churn import config
from churn.feature_engineering import add_engineered_features
from churn.preprocessing import ChurnPreprocessor, clean, label_first, merge_sources, split, transformed_feature_names


def _frame(n=400, seed=0):
    from churn.data.generate_synthetic import _population

    df = _population(np.random.default_rng(seed), n, 1)
    df["churn"] = np.where(np.arange(n) % 5 == 0, "Yes", "No")
    return add_engineered_features(clean(df))


def test_merge_and_clean_drop_duplicates_and_encode_label():
    customers = pd.DataFrame({"customer_id": [1, 1, 2], "age": [30, 30, 40]})
    churn = pd.DataFrame({"customer_id": [1, 2], "churn": ["Yes", "No"]})
    merged = clean(merge_sources({"customers": customers, "churn": churn}))
    assert len(merged) == 2
    assert merged.set_index("customer_id")["churn"].to_dict() == {1: 1, 2: 0}


def test_split_is_stratified():
    train, validation, test = split(_frame(2000))
    rates = [f["churn"].mean() for f in (train, validation, test)]
    assert max(rates) - min(rates) < 0.01
    assert len(train) == 1400 and len(validation) == 300 and len(test) == 300


def test_encoded_columns_are_deterministic_and_match_names():
    cols = config.model_input_columns()
    pre = ChurnPreprocessor().fit(_frame()[cols])
    matrix = pre.transform(_frame(50, seed=3)[cols])
    assert matrix.shape[1] == len(transformed_feature_names())
    assert list(pre.get_feature_names_out()) == transformed_feature_names()


def test_fit_on_train_only_and_unseen_or_missing_categories_go_to_unknown():
    cols = config.model_input_columns()
    pre = ChurnPreprocessor().fit(_frame()[cols])
    row = _frame(1, seed=5)[cols].copy()
    row["region"] = "Mars"
    row["gender"] = None
    row["monthly_charges"] = np.nan
    encoded = dict(zip(transformed_feature_names(), pre.transform(row)[0]))
    assert encoded["region=Unknown"] == 1.0 and encoded["gender=Unknown"] == 1.0
    assert encoded["monthly_charges_was_missing"] == 1.0
    assert np.isfinite(list(encoded.values())).all()


def test_outliers_are_capped_at_train_fences():
    cols = config.model_input_columns()
    pre = ChurnPreprocessor().fit(_frame()[cols])
    row = _frame(1, seed=6)[cols].copy()
    row["monthly_charges"] = 1e9
    idx = transformed_feature_names().index("monthly_charges")
    capped = (pre.upper_["monthly_charges"] - pre.means_["monthly_charges"]) / pre.stds_["monthly_charges"]
    assert np.isclose(pre.transform(row)[0][idx], capped)


def test_preprocessor_pickles_and_label_first_layout():
    cols = config.model_input_columns()
    frame = _frame()
    pre = pickle.loads(pickle.dumps(ChurnPreprocessor().fit(frame[cols])))
    out = label_first(pre.transform(frame[cols]), frame["churn"])
    assert set(np.unique(out[:, 0])) == {0.0, 1.0}
