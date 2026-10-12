import json
import subprocess

import pytest

from churn.deploy import canary_analysis as ca
from churn.deploy.common import EXIT_FAIL, EXIT_INCONCLUSIVE, EXIT_PASS

from .fakes import FakeClock, FakeProm

HIST = {0.1: 500.0, 0.3: 800.0, 0.5: 900.0, 1.0: 950.0, float("inf"): 1000.0}
SHIFTED = {0.1: 100.0, 0.3: 200.0, 0.5: 400.0, 1.0: 900.0, float("inf"): 1000.0}
ARGS = [
    "--namespace",
    "churn-serving",
    "--isvc",
    "churn-lgbm",
    "--max-p99-ms",
    "150",
    "--max-error-rate",
    "0.001",
    "--max-score-psi",
    "0.1",
]


def args(*extra):
    return ca.build_parser().parse_args([*ARGS, *extra])


def snapshot(requests=1000.0, error_rate=0.0, p99=80.0, hist=HIST):
    return {
        "requests": requests,
        "error_rate": error_rate,
        "p99_ms": p99,
        "score_hist": {str(k): v for k, v in hist.items()},
    }


def test_evaluate_pass():
    code, checks = ca.evaluate(snapshot(), snapshot(p99=75.0), args())
    assert code == EXIT_PASS
    assert all(c["ok"] for c in checks)


@pytest.mark.parametrize(
    ("canary", "failing"),
    [
        (snapshot(error_rate=0.01), "error_rate"),
        (snapshot(p99=160.0), "p99_ms"),
        (snapshot(hist=SHIFTED), "score_psi"),
    ],
)
def test_evaluate_breach(canary, failing):
    code, checks = ca.evaluate(canary, snapshot(p99=140.0), args())
    assert code == EXIT_FAIL
    assert [c["check"] for c in checks if c["ok"] is False] == [failing]


def test_p99_regression_vs_stable():
    code, checks = ca.evaluate(snapshot(p99=120.0), snapshot(p99=60.0), args())
    assert code == EXIT_FAIL
    assert [c["check"] for c in checks if c["ok"] is False] == ["p99_regression_vs_stable"]


def test_insufficient_traffic_is_inconclusive():
    code, _ = ca.evaluate(snapshot(requests=10, error_rate=0.5), snapshot(), args())
    assert code == EXIT_INCONCLUSIVE


def test_missing_score_histogram_is_inconclusive():
    code, _ = ca.evaluate(snapshot(hist={}), snapshot(), args())
    assert code == EXIT_INCONCLUSIVE


def test_revisions_from_traffic_status():
    isvc = {
        "status": {
            "components": {
                "transformer": {
                    "traffic": [
                        {
                            "revisionName": "churn-lgbm-transformer-00002",
                            "latestRevision": True,
                            "percent": 10,
                        },
                        {
                            "revisionName": "churn-lgbm-transformer-00001",
                            "latestRevision": False,
                            "tag": "prev",
                            "percent": 90,
                        },
                    ]
                }
            }
        }
    }
    assert ca.revisions_from_status(isvc, "transformer") == (
        "churn-lgbm-transformer-00002",
        "churn-lgbm-transformer-00001",
    )


def test_revisions_fallback_fields_and_error():
    isvc = {
        "status": {
            "components": {
                "predictor": {
                    "latestReadyRevision": "p-00003",
                    "previousRolledoutRevision": "p-00002",
                }
            }
        }
    }
    assert ca.revisions_from_status(isvc, "predictor") == ("p-00003", "p-00002")
    with pytest.raises(RuntimeError):
        ca.revisions_from_status({"status": {}}, "transformer")


def test_resolve_revisions_uses_kubectl(monkeypatch):
    status = {
        "status": {
            "components": {
                "transformer": {"latestReadyRevision": "t-2", "previousRolledoutRevision": "t-1"}
            }
        }
    }
    monkeypatch.setattr(ca.shutil, "which", lambda _: "/usr/bin/kubectl")
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(status))

    monkeypatch.setattr(ca.subprocess, "run", fake_run)
    assert ca.resolve_revisions("churn-lgbm", "churn-serving", "transformer") == ("t-2", "t-1")
    assert seen["cmd"][:4] == ["/usr/bin/kubectl", "get", "isvc", "churn-lgbm"]


def test_resolve_revisions_without_kubectl(monkeypatch):
    monkeypatch.setattr(ca.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError):
        ca.resolve_revisions("i", "n", "transformer")


def make_prom(canary_p99=80.0, canary_errors=0.0):
    return FakeProm(
        scalars=[
            (r'canary-deployment".*response_code', canary_errors),
            (r'stable-deployment".*response_code', 0.0),
            (r"histogram_quantile.*canary-deployment", canary_p99),
            (r"histogram_quantile.*stable-deployment", 75.0),
            (r"canary-deployment", 1000.0),
            (r"stable-deployment", 9000.0),
        ],
        histograms=[(r'revision="canary"', HIST), (r'revision="stable"', HIST)],
    )


def test_main_polls_full_window_and_promotes(tmp_path):
    clock = FakeClock()
    prom = make_prom()
    out, summary = tmp_path / "decision.json", tmp_path / "summary.md"
    code = ca.main(
        [
            *ARGS,
            "--prometheus-url",
            "https://amw.example",
            "--window",
            "3m",
            "--interval",
            "60s",
            "--canary-revision",
            "canary",
            "--stable-revision",
            "stable",
            "--output",
            str(out),
            "--summary",
            str(summary),
        ],
        prom=prom,
        clock=clock,
        sleep=clock.sleep,
    )
    assert code == EXIT_PASS
    assert clock.sleeps == [60, 60, 60]
    assert json.loads(out.read_text())["exit_code"] == 0
    assert "PROMOTE" in summary.read_text()
    assert any('destination_workload="canary-deployment"' in q for q in prom.queries)


def test_main_fails_fast_on_breach(tmp_path):
    clock = FakeClock()
    code = ca.main(
        [
            *ARGS,
            "--prometheus-url",
            "https://amw.example",
            "--window",
            "30m",
            "--canary-revision",
            "canary",
            "--stable-revision",
            "stable",
            "--summary",
            str(tmp_path / "s.md"),
        ],
        prom=make_prom(canary_errors=50.0),
        clock=clock,
        sleep=clock.sleep,
    )
    assert code == EXIT_FAIL
    assert clock.sleeps == [60]


def test_main_input_json(tmp_path):
    snap = tmp_path / "snap.json"
    snap.write_text(json.dumps({"canary": snapshot(), "stable": snapshot()}))
    assert ca.main([*ARGS, "--input-json", str(snap), "--summary", str(tmp_path / "s")]) == 0


def test_main_requires_prometheus_url(tmp_path):
    assert ca.main([*ARGS, "--summary", str(tmp_path / "s")]) == EXIT_INCONCLUSIVE
