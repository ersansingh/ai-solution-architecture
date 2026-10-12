import math

from churn import config
from churn.feature_store import feature_types, from_record, to_record


def test_record_roundtrip_skips_missing_and_restores_types():
    row = {c: 1.5 for c in config.numeric_columns()}
    row.update({c: "x" for c in config.categorical_columns()})
    row["satisfaction_score"] = math.nan
    row["region"] = None
    record = to_record({"customer_id": "42", **row})
    names = {r["FeatureName"] for r in record}
    assert "satisfaction_score" not in names and "region" not in names
    back = from_record(record)
    assert back["satisfaction_score"] is None and back["region"] is None
    assert back["tenure_months"] == 1.5 and back["gender"] == "x"
    assert list(back) == config.model_input_columns()


def test_feature_types_cover_contract():
    types = feature_types()
    assert types["customer_id"] == "String" and types["event_time"] == "String"
    assert all(types[c] == "Fractional" for c in config.numeric_columns())
