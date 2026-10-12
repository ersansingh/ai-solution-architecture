import json
from pathlib import Path

import pytest

from churn.data_contracts import run as dc

ROOT = Path(__file__).resolve().parents[2]
SUITES = [
    ROOT / "data_contracts/gold_customer_features.json",
    ROOT / "data_contracts/silver_billing.json",
]
SAMPLES = ROOT / "tests/fixtures/contract_samples"


def test_versioned_suites_pass_on_fixtures(tmp_path):
    out = tmp_path / "results.json"
    argv = [a for s in SUITES for a in ("--suite", str(s))]
    code = dc.main([*argv, "--data", str(SAMPLES), "--fail-on-error", "--output", str(out)])
    assert code == 0
    assert all(r["success"] for r in json.loads(out.read_text()))


def write(tmp_path, rows, header):
    path = tmp_path / "t.csv"
    path.write_text("\n".join([",".join(header), *[",".join(r) for r in rows]]) + "\n")
    return path


@pytest.mark.parametrize(
    ("etype", "kwargs", "rows", "ok"),
    [
        ("expect_column_values_to_not_be_null", {"column": "a"}, [["1", "x"], ["", "y"]], False),
        (
            "expect_column_values_to_not_be_null",
            {"column": "a", "mostly": 0.5},
            [["1", "x"], ["", "y"]],
            True,
        ),
        (
            "expect_column_values_to_be_between",
            {"column": "a", "min_value": 0, "strict_min": True},
            [["0", "x"]],
            False,
        ),
        (
            "expect_column_values_to_be_between",
            {"column": "a", "max_value": 5, "strict_max": True},
            [["5", "x"]],
            False,
        ),
        (
            "expect_column_values_to_be_between",
            {"column": "a", "max_value": 5},
            [["9", "x"]],
            False,
        ),
        (
            "expect_column_values_to_be_between",
            {"column": "a", "min_value": 0},
            [["n/a", "x"]],
            False,
        ),
        (
            "expect_column_values_to_match_regex",
            {"column": "b", "regex": "^[xy]$"},
            [["1", "x"], ["2", "z"]],
            False,
        ),
        (
            "expect_column_values_to_be_in_set",
            {"column": "b", "value_set": ["x"]},
            [["1", "y"]],
            False,
        ),
        ("expect_column_values_to_be_unique", {"column": "a"}, [["1", "x"], ["1", "y"]], False),
        (
            "expect_compound_columns_to_be_unique",
            {"column_list": ["a", "b"]},
            [["1", "x"], ["1", "y"]],
            True,
        ),
        ("expect_table_row_count_to_be_between", {"min_value": 3}, [["1", "x"]], False),
        (
            "expect_table_columns_to_match_set",
            {"column_set": ["a"], "exact_match": False},
            [["1", "x"]],
            True,
        ),
        ("expect_table_columns_to_match_set", {"column_set": ["a"]}, [["1", "x"]], False),
        (
            "expect_column_pair_values_a_to_be_greater_than_b",
            {"column_A": "a", "column_B": "b", "or_equal": True},
            [["2026-01-02", "2026-01-02"]],
            True,
        ),
        (
            "expect_column_pair_values_a_to_be_greater_than_b",
            {"column_A": "a", "column_B": "b"},
            [["2026-01-01", "2026-01-02T10:00:00Z"]],
            False,
        ),
        (
            "expect_column_pair_values_a_to_be_greater_than_b",
            {"column_A": "a", "column_B": "b"},
            [["3", "2"]],
            True,
        ),
        ("expect_column_mean_to_be_between", {"column": "a"}, [["1", "x"]], False),
        ("expect_column_values_to_not_be_null", {"column": "missing"}, [["1", "x"]], False),
    ],
)
def test_expectations(tmp_path, etype, kwargs, rows, ok):
    write(tmp_path, rows, ["a", "b"])
    suite = {
        "name": "t",
        "meta": {"data_asset": "t.csv"},
        "expectations": [{"type": etype, "kwargs": kwargs}],
    }
    [result] = dc.validate_suite(suite, tmp_path)
    assert result["success"] is ok


def test_missing_asset_and_fail_on_error(tmp_path):
    suite = tmp_path / "s.json"
    suite.write_text(json.dumps({"name": "absent", "expectations": []}))
    assert dc.main(["--suite", str(suite), "--data", str(tmp_path)]) == 0
    assert dc.main(["--suite", str(suite), "--data", str(tmp_path), "--fail-on-error"]) == 1


def test_bad_suite_returns_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert dc.main(["--suite", str(bad), "--data", str(tmp_path)]) == 2
