"""Validate CSV fixtures against versioned data-contract suites.

Suites (``data_contracts/*.json``) use the Great Expectations 1.x
expectation-suite JSON layout (``name``, ``expectations[].type``,
``expectations[].kwargs``) plus a ``meta.data_asset`` file name. The same
suites run with GX on Databricks at pipeline runtime; in CI this stdlib
evaluator checks the sampled fixtures without a Spark/GX data context.

Supported expectation types are listed in ``EXPECTATIONS``; an unknown type
is reported as a failure so contracts never silently pass.

Usage::

    python -m churn.data_contracts.run --suite data_contracts/a.json \\
        --suite data_contracts/b.json --data tests/fixtures/contract_samples --fail-on-error
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

Rows = list[dict[str, str]]


def _num(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cmp_value(v: str) -> Any:
    """Compare as number when numeric, else as ISO date, else as string."""
    n = _num(v)
    if n is not None:
        return n
    try:
        return date.fromisoformat(v[:10])
    except ValueError:
        return v


def _mostly(failures: int, total: int, kwargs: dict) -> bool:
    if total == 0:
        return True
    return (total - failures) / total >= float(kwargs.get("mostly", 1.0))


def _non_null(rows: Rows, col: str) -> list[str]:
    return [r[col] for r in rows if r.get(col) not in (None, "")]


def exp_table_columns_to_match_set(rows: Rows, cols: list[str], kw: dict) -> tuple[bool, str]:
    want = set(kw["column_set"])
    have = set(cols)
    exact = kw.get("exact_match", True)
    ok = have == want if exact else want <= have
    return ok, f"missing={sorted(want - have)} unexpected={sorted(have - want) if exact else []}"


def exp_table_row_count_to_be_between(rows: Rows, cols: list[str], kw: dict) -> tuple[bool, str]:
    n = len(rows)
    lo, hi = kw.get("min_value"), kw.get("max_value")
    ok = (lo is None or n >= lo) and (hi is None or n <= hi)
    return ok, f"rows={n}"


def exp_column_values_to_not_be_null(rows: Rows, cols: list[str], kw: dict) -> tuple[bool, str]:
    col = kw["column"]
    nulls = sum(1 for r in rows if r.get(col) in (None, ""))
    return _mostly(nulls, len(rows), kw), f"nulls={nulls}"


def exp_column_values_to_be_between(rows: Rows, cols: list[str], kw: dict) -> tuple[bool, str]:
    col = kw["column"]
    lo, hi = kw.get("min_value"), kw.get("max_value")
    strict_lo, strict_hi = kw.get("strict_min", False), kw.get("strict_max", False)
    values = _non_null(rows, col)
    bad = 0
    for v in values:
        n = _num(v)
        if n is None:
            bad += 1
        elif lo is not None and (n < lo or (strict_lo and n == lo)):
            bad += 1
        elif hi is not None and (n > hi or (strict_hi and n == hi)):
            bad += 1
    return _mostly(bad, len(values), kw), f"out_of_range={bad}"


def exp_column_values_to_match_regex(rows: Rows, cols: list[str], kw: dict) -> tuple[bool, str]:
    pattern = re.compile(kw["regex"])
    values = _non_null(rows, kw["column"])
    bad = sum(1 for v in values if not pattern.search(v))
    return _mostly(bad, len(values), kw), f"non_matching={bad}"


def exp_column_values_to_be_in_set(rows: Rows, cols: list[str], kw: dict) -> tuple[bool, str]:
    allowed = {str(v) for v in kw["value_set"]}
    values = _non_null(rows, kw["column"])
    bad = sorted({v for v in values if v not in allowed})
    count = sum(1 for v in values if v not in allowed)
    return _mostly(count, len(values), kw), f"unexpected={bad[:5]}"


def exp_column_values_to_be_unique(rows: Rows, cols: list[str], kw: dict) -> tuple[bool, str]:
    values = _non_null(rows, kw["column"])
    dupes = len(values) - len(set(values))
    return dupes == 0, f"duplicates={dupes}"


def exp_compound_columns_to_be_unique(rows: Rows, cols: list[str], kw: dict) -> tuple[bool, str]:
    keys = [tuple(r.get(c, "") for c in kw["column_list"]) for r in rows]
    dupes = len(keys) - len(set(keys))
    return dupes == 0, f"duplicates={dupes}"


def exp_column_pair_values_a_to_be_greater_than_b(
    rows: Rows, cols: list[str], kw: dict
) -> tuple[bool, str]:
    a, b, or_equal = kw["column_A"], kw["column_B"], kw.get("or_equal", False)
    pairs = [(r[a], r[b]) for r in rows if r.get(a) and r.get(b)]
    bad = 0
    for va, vb in pairs:
        ca, cb = _cmp_value(va), _cmp_value(vb)
        if type(ca) is not type(cb) or not (ca > cb or (or_equal and ca == cb)):
            bad += 1
    return _mostly(bad, len(pairs), kw), f"violations={bad}"


EXPECTATIONS: dict[str, Callable[[Rows, list[str], dict], tuple[bool, str]]] = {
    "expect_table_columns_to_match_set": exp_table_columns_to_match_set,
    "expect_table_row_count_to_be_between": exp_table_row_count_to_be_between,
    "expect_column_values_to_not_be_null": exp_column_values_to_not_be_null,
    "expect_column_values_to_be_between": exp_column_values_to_be_between,
    "expect_column_values_to_match_regex": exp_column_values_to_match_regex,
    "expect_column_values_to_be_in_set": exp_column_values_to_be_in_set,
    "expect_column_values_to_be_unique": exp_column_values_to_be_unique,
    "expect_compound_columns_to_be_unique": exp_compound_columns_to_be_unique,
    "expect_column_pair_values_a_to_be_greater_than_b": (
        exp_column_pair_values_a_to_be_greater_than_b
    ),
}


def load_csv(path: Path) -> tuple[Rows, list[str]]:
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def validate_suite(suite: dict, data_dir: Path) -> list[dict]:
    asset = suite.get("meta", {}).get("data_asset") or f"{suite['name']}.csv"
    path = data_dir / asset
    if not path.is_file():
        return [
            {
                "suite": suite["name"],
                "type": "data_asset_exists",
                "success": False,
                "detail": f"{path} not found",
            }
        ]
    rows, cols = load_csv(path)
    results = []
    for exp in suite.get("expectations", []):
        etype, kwargs = exp.get("type", ""), exp.get("kwargs", {})
        fn = EXPECTATIONS.get(etype)
        if fn is None:
            ok, detail = False, "unsupported expectation type"
        else:
            try:
                ok, detail = fn(rows, cols, kwargs)
            except KeyError as exc:
                ok, detail = False, f"missing column/kwarg {exc}"
        results.append(
            {
                "suite": suite["name"],
                "type": etype,
                "column": kwargs.get("column"),
                "success": ok,
                "detail": detail,
            }
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m churn.data_contracts.run", description=__doc__)
    p.add_argument("--suite", action="append", required=True, type=Path, help="suite JSON")
    p.add_argument("--data", required=True, type=Path, help="directory with CSV samples")
    p.add_argument("--fail-on-error", action="store_true", help="exit 1 on any failure")
    p.add_argument("--output", type=Path, help="write results JSON here")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results: list[dict] = []
    for suite_path in args.suite:
        try:
            suite = json.loads(suite_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: cannot load suite {suite_path}: {exc}", file=sys.stderr)
            return 2
        results.extend(validate_suite(suite, args.data))

    failed = [r for r in results if not r["success"]]
    for r in results:
        status = "PASS" if r["success"] else "FAIL"
        col = f"[{r['column']}]" if r.get("column") else ""
        print(f"{status} {r['suite']} {r['type']}{col}: {r['detail']}")
    print(f"{len(results) - len(failed)}/{len(results)} expectations passed")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2))
    return 1 if failed and args.fail_on_error else 0


if __name__ == "__main__":
    sys.exit(main())
