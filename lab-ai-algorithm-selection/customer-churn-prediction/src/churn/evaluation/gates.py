"""Champion/challenger evaluation gates (system-design.md sections 1.4, 6.4, 7.10).

Reads ``<report>/metrics.json`` written by the Azure ML ``evaluate`` component
(``pipelines/aml/src/evaluate.py``), applies every gate, writes
``<report>/gates.json`` and exits non-zero if any gate fails.

Exit codes: 0 = all gates passed, 1 = at least one gate failed,
2 = the report is missing or malformed.

Gates (a missing metric always fails its gate):

1. Out-of-time PR-AUC >= champion PR-AUC + uplift; recall@top-decile not worse
2. ROC-AUC >= 0.88 (go-live gate) and significantly better than the WoE LR baseline
3. Lift@top-decile >= 4x
4. Tier A precision >= 0.85, Tier B recall >= 0.80
5. Calibration: ECE <= max, Brier score not worse than champion
6. Fairness per protected attribute: disparate impact, equal-opportunity
   (TPR) difference and FPR difference
7. Latency: p99 precomputed and p99 rescoring+SHAP paths
8. SHAP sanity: no single feature > 40% of global importance
9. Leakage: no single feature with AUC >= 0.95
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

METRICS_FILE = "metrics.json"
GATES_FILE = "gates.json"


@dataclass
class GateResult:
    name: str
    passed: bool
    actual: float | None
    threshold: float | None
    detail: str = ""


def _get(d: dict[str, Any] | None, *keys: str) -> float | None:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    if isinstance(cur, bool) or cur is None:
        return None
    try:
        return float(cur)
    except (TypeError, ValueError):
        return None


def _min_gate(name: str, actual: float | None, threshold: float) -> GateResult:
    if actual is None:
        return GateResult(name, False, None, threshold, "metric missing")
    return GateResult(name, actual >= threshold, actual, threshold, ">=")


def _max_gate(name: str, actual: float | None, threshold: float) -> GateResult:
    if actual is None:
        return GateResult(name, False, None, threshold, "metric missing")
    return GateResult(name, actual <= threshold, actual, threshold, "<=")


def _gt_gate(name: str, actual: float | None, threshold: float) -> GateResult:
    if actual is None:
        return GateResult(name, False, None, threshold, "metric missing")
    return GateResult(name, actual > threshold, actual, threshold, ">")


def _lt_gate(name: str, actual: float | None, threshold: float) -> GateResult:
    if actual is None:
        return GateResult(name, False, None, threshold, "metric missing")
    return GateResult(name, actual < threshold, actual, threshold, "<")


def champion_from_registry(model_name: str, alias: str) -> dict[str, Any] | None:
    """Fallback: read champion metrics from MLflow model-version tags.

    ``register-model`` in the GitHub pipeline tags each version with
    ``oot_pr_auc``. Returns None when MLflow is unavailable or no champion exists
    (first release).
    """
    try:
        from mlflow import MlflowClient
    except ImportError:
        return None
    try:
        mv = MlflowClient().get_model_version_by_alias(model_name, alias)
    except Exception:
        return None
    tags = mv.tags or {}
    champ: dict[str, Any] = {"model_version": mv.version}
    for key, tag in (("pr_auc", "oot_pr_auc"), ("brier", "oot_brier")):
        if tag in tags:
            champ[key] = tags[tag]
    return champ


def evaluate_gates(metrics: dict[str, Any], args: argparse.Namespace) -> list[GateResult]:
    cand = metrics.get("candidate") or {}
    champ = metrics.get("champion")
    results: list[GateResult] = []

    # Gate 1: PR-AUC vs champion (+ recall@top-decile)
    cand_pr = _get(cand, "pr_auc")
    champ_pr = _get(champ, "pr_auc")
    if champ_pr is None:
        results.append(
            GateResult(
                "pr_auc_vs_champion",
                cand_pr is not None,
                cand_pr,
                None,
                f"no '{args.champion_alias}' champion for {args.model_name}: first release",
            )
        )
    else:
        results.append(_min_gate("pr_auc_vs_champion", cand_pr, champ_pr + args.min_pr_auc_uplift))
        champ_rtd = _get(champ, "recall_top_decile")
        if champ_rtd is not None:
            results.append(
                _min_gate(
                    "recall_top_decile_vs_champion", _get(cand, "recall_top_decile"), champ_rtd
                )
            )

    # Gate 2: ROC-AUC go-live floor and significance over the WoE LR baseline
    results.append(_min_gate("roc_auc", _get(cand, "roc_auc"), args.min_roc_auc))
    results.append(
        _gt_gate(
            "roc_auc_gain_over_lr_baseline_ci_low",
            _get(metrics, "baseline", "roc_auc_delta_ci_low"),
            0.0,
        )
    )

    # Gate 3/4: lift and operating tiers
    results.append(_min_gate("lift_top_decile", _get(cand, "lift_top_decile"), args.min_lift))
    results.append(
        _min_gate("tier_a_precision", _get(cand, "tier_a_precision"), args.min_tier_a_precision)
    )
    results.append(_min_gate("tier_b_recall", _get(cand, "tier_b_recall"), args.min_tier_b_recall))

    # Gate 5: calibration
    results.append(_max_gate("ece", _get(cand, "ece"), args.max_ece))
    champ_brier = _get(champ, "brier")
    if champ_brier is not None:
        results.append(_max_gate("brier_vs_champion", _get(cand, "brier"), champ_brier))

    # Gate 6: fairness across every audited attribute
    fairness = metrics.get("fairness") or {}
    if not fairness:
        results.append(GateResult("fairness", False, None, None, "fairness section missing"))
    for attr in sorted(fairness):
        results.append(
            _min_gate(
                f"fairness_{attr}_disparate_impact",
                _get(fairness, attr, "disparate_impact"),
                args.min_disparate_impact,
            )
        )
        results.append(
            _max_gate(
                f"fairness_{attr}_equal_opportunity_diff",
                _get(fairness, attr, "equal_opportunity_diff"),
                args.max_equal_opp_diff,
            )
        )
        results.append(
            _max_gate(
                f"fairness_{attr}_fpr_diff",
                _get(fairness, attr, "fpr_diff"),
                args.max_fpr_diff,
            )
        )

    # Gate 7: latency
    results.append(
        _max_gate(
            "p99_precomputed_ms",
            _get(metrics, "latency", "p99_precomputed_ms"),
            args.max_p99_latency_ms,
        )
    )
    results.append(
        _max_gate(
            "p99_rescore_ms", _get(metrics, "latency", "p99_rescore_ms"), args.max_p99_rescore_ms
        )
    )

    # Gate 8/9: SHAP concentration and leakage sanity
    results.append(
        _max_gate("shap_max_feature_share", _get(cand, "shap_max_share"), args.max_shap_share)
    )
    results.append(
        _lt_gate(
            "max_single_feature_auc",
            _get(metrics, "leakage", "max_single_feature_auc"),
            args.max_single_feature_auc,
        )
    )
    return results


def _fmt(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.4f}"


def render_summary(results: list[GateResult], run_id: str, model_name: str) -> str:
    passed = all(r.passed for r in results)
    lines = [
        f"## Evaluation gates: {'PASSED' if passed else 'FAILED'}",
        "",
        f"Model `{model_name}`, candidate run `{run_id or 'unknown'}`",
        "",
        "| Gate | Result | Actual | Threshold | Note |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r.name} | {'pass' if r.passed else 'FAIL'} | {_fmt(r.actual)} "
            f"| {_fmt(r.threshold)} | {r.detail} |"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m churn.evaluation.gates", description=__doc__)
    p.add_argument("--report", required=True, type=Path, help="evaluation_report directory")
    p.add_argument("--champion-alias", default="champion")
    p.add_argument("--model-name", required=True)
    p.add_argument("--min-pr-auc-uplift", type=float, default=0.005)
    p.add_argument("--max-ece", type=float, default=0.02)
    p.add_argument("--min-disparate-impact", type=float, default=0.80)
    p.add_argument("--max-equal-opp-diff", type=float, default=0.05)
    p.add_argument("--max-fpr-diff", type=float, default=0.05)
    p.add_argument("--max-p99-latency-ms", type=float, default=50.0)
    p.add_argument("--max-p99-rescore-ms", type=float, default=150.0)
    p.add_argument("--min-roc-auc", type=float, default=0.88)
    p.add_argument("--min-lift", type=float, default=4.0, help="lift@top-decile floor")
    p.add_argument("--min-tier-a-precision", type=float, default=0.85)
    p.add_argument("--min-tier-b-recall", type=float, default=0.80)
    p.add_argument("--max-shap-share", type=float, default=0.40)
    p.add_argument("--max-single-feature-auc", type=float, default=0.95)
    p.add_argument("--github-output", type=Path, help="append step outputs ($GITHUB_OUTPUT)")
    p.add_argument("--summary", type=Path, help="append markdown ($GITHUB_STEP_SUMMARY)")
    return p


def main(
    argv: list[str] | None = None,
    champion_lookup: Callable[[str, str], dict[str, Any] | None] = champion_from_registry,
) -> int:
    args = build_parser().parse_args(argv)
    metrics_path = args.report / METRICS_FILE
    try:
        metrics = json.loads(metrics_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {metrics_path}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(metrics, dict) or not isinstance(metrics.get("candidate"), dict):
        print(f"ERROR: {metrics_path} has no 'candidate' section", file=sys.stderr)
        return 2

    if _get(metrics.get("champion"), "pr_auc") is None:
        champ = champion_lookup(args.model_name, args.champion_alias)
        if champ:
            metrics["champion"] = champ

    results = evaluate_gates(metrics, args)
    passed = all(r.passed for r in results)
    run_id = str(metrics["candidate"].get("run_id", ""))
    pr_auc = _get(metrics["candidate"], "pr_auc")

    (args.report / GATES_FILE).write_text(
        json.dumps(
            {
                "passed": passed,
                "model_name": args.model_name,
                "candidate_run_id": run_id,
                "champion": metrics.get("champion"),
                "gates": [asdict(r) for r in results],
            },
            indent=2,
        )
    )
    summary = render_summary(results, run_id, args.model_name)
    print(summary)
    if args.summary:
        with args.summary.open("a") as fh:
            fh.write(summary)
    if args.github_output:
        with args.github_output.open("a") as fh:
            fh.write(f"run_id={run_id}\n")
            fh.write(f"pr_auc={'' if pr_auc is None else f'{pr_auc:.6f}'}\n")
            fh.write(f"passed={str(passed).lower()}\n")
    if not run_id:
        print("ERROR: candidate.run_id missing; cannot register the model", file=sys.stderr)
        return 2
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
