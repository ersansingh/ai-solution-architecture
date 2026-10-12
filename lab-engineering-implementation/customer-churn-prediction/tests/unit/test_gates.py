import json

import pytest

from churn.evaluation import gates

BASE_ARGS = [
    "--model-name",
    "churn-lightgbm",
    "--champion-alias",
    "champion",
    "--min-pr-auc-uplift",
    "0.005",
    "--max-ece",
    "0.02",
    "--min-disparate-impact",
    "0.80",
    "--max-equal-opp-diff",
    "0.05",
    "--max-p99-latency-ms",
    "50",
    "--max-p99-rescore-ms",
    "150",
]


def good_metrics():
    fair = {"disparate_impact": 0.92, "equal_opportunity_diff": 0.02, "fpr_diff": 0.01}
    return {
        "candidate": {
            "run_id": "run-123",
            "algorithm": "lightgbm",
            "pr_auc": 0.61,
            "roc_auc": 0.90,
            "lift_top_decile": 4.6,
            "recall_top_decile": 0.47,
            "brier": 0.041,
            "ece": 0.012,
            "tier_a_precision": 0.87,
            "tier_b_recall": 0.82,
            "shap_max_share": 0.21,
        },
        "champion": {"pr_auc": 0.60, "recall_top_decile": 0.45, "brier": 0.043},
        "baseline": {"roc_auc_delta_ci_low": 0.03},
        "fairness": {"age_band": fair, "gender": fair, "region": fair},
        "latency": {"p99_precomputed_ms": 12.0, "p99_rescore_ms": 95.0},
        "leakage": {"max_single_feature_auc": 0.71},
    }


def write_report(tmp_path, metrics):
    report = tmp_path / "evaluation_report"
    report.mkdir()
    (report / "metrics.json").write_text(json.dumps(metrics))
    return report


def run(tmp_path, metrics, extra=(), lookup=lambda name, alias: None):
    report = write_report(tmp_path, metrics)
    out, summary = tmp_path / "gh_output", tmp_path / "summary.md"
    argv = [
        "--report",
        str(report),
        *BASE_ARGS,
        "--github-output",
        str(out),
        "--summary",
        str(summary),
        *extra,
    ]
    code = gates.main(argv, champion_lookup=lookup)
    return code, report, out, summary


def failed_gates(report):
    data = json.loads((report / "gates.json").read_text())
    return {g["name"] for g in data["gates"] if not g["passed"]}


def test_all_gates_pass_and_outputs_written(tmp_path):
    code, report, out, summary = run(tmp_path, good_metrics())
    assert code == 0
    assert failed_gates(report) == set()
    text = out.read_text()
    assert "run_id=run-123\n" in text
    assert "pr_auc=0.610000\n" in text
    assert "passed=true" in text
    assert "PASSED" in summary.read_text()


@pytest.mark.parametrize(
    ("path", "value", "gate"),
    [
        (("candidate", "pr_auc"), 0.603, "pr_auc_vs_champion"),
        (("candidate", "recall_top_decile"), 0.40, "recall_top_decile_vs_champion"),
        (("candidate", "roc_auc"), 0.87, "roc_auc"),
        (("baseline", "roc_auc_delta_ci_low"), 0.0, "roc_auc_gain_over_lr_baseline_ci_low"),
        (("candidate", "lift_top_decile"), 3.5, "lift_top_decile"),
        (("candidate", "tier_a_precision"), 0.80, "tier_a_precision"),
        (("candidate", "tier_b_recall"), 0.75, "tier_b_recall"),
        (("candidate", "ece"), 0.025, "ece"),
        (("candidate", "brier"), 0.05, "brier_vs_champion"),
        (("latency", "p99_precomputed_ms"), 51, "p99_precomputed_ms"),
        (("latency", "p99_rescore_ms"), 151, "p99_rescore_ms"),
        (("candidate", "shap_max_share"), 0.45, "shap_max_feature_share"),
        (("leakage", "max_single_feature_auc"), 0.95, "max_single_feature_auc"),
    ],
)
def test_each_gate_fails(tmp_path, path, value, gate):
    metrics = good_metrics()
    metrics[path[0]][path[1]] = value
    code, report, out, _ = run(tmp_path, metrics)
    assert code == 1
    assert failed_gates(report) == {gate}
    assert "passed=false" in out.read_text()


def test_fairness_breach_per_attribute(tmp_path):
    metrics = good_metrics()
    metrics["fairness"]["region"] = {
        "disparate_impact": 0.70,
        "equal_opportunity_diff": 0.08,
        "fpr_diff": 0.06,
    }
    code, report, _, _ = run(tmp_path, metrics)
    assert code == 1
    assert failed_gates(report) == {
        "fairness_region_disparate_impact",
        "fairness_region_equal_opportunity_diff",
        "fairness_region_fpr_diff",
    }


def test_missing_metric_fails_closed(tmp_path):
    metrics = good_metrics()
    del metrics["candidate"]["tier_b_recall"]
    del metrics["fairness"]
    code, report, _, _ = run(tmp_path, metrics)
    assert code == 1
    assert {"tier_b_recall", "fairness"} <= failed_gates(report)


def test_first_release_without_champion(tmp_path):
    metrics = good_metrics()
    metrics["champion"] = None
    code, report, _, _ = run(tmp_path, metrics)
    assert code == 0
    gate = next(
        g
        for g in json.loads((report / "gates.json").read_text())["gates"]
        if g["name"] == "pr_auc_vs_champion"
    )
    assert "first release" in gate["detail"]


def test_champion_from_registry_fallback(tmp_path):
    metrics = good_metrics()
    metrics["champion"] = None
    calls = []

    def lookup(name, alias):
        calls.append((name, alias))
        return {"pr_auc": "0.62", "model_version": "7"}

    code, report, _, _ = run(tmp_path, metrics, lookup=lookup)
    assert calls == [("churn-lightgbm", "champion")]
    assert code == 1
    assert failed_gates(report) == {"pr_auc_vs_champion"}


def test_cli_threshold_override(tmp_path):
    metrics = good_metrics()
    metrics["candidate"]["roc_auc"] = 0.86
    code, _, _, _ = run(tmp_path, metrics, extra=["--min-roc-auc", "0.85"])
    assert code == 0


def test_missing_report_returns_2(tmp_path):
    assert gates.main(["--report", str(tmp_path / "nope"), "--model-name", "m"]) == 2


def test_report_without_candidate_returns_2(tmp_path):
    code, _, _, _ = run(tmp_path, {"champion": {}})
    assert code == 2


def test_missing_run_id_returns_2(tmp_path):
    metrics = good_metrics()
    del metrics["candidate"]["run_id"]
    code, _, _, _ = run(tmp_path, metrics)
    assert code == 2


def test_champion_from_registry_without_mlflow(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "mlflow":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert gates.champion_from_registry("m", "champion") is None
