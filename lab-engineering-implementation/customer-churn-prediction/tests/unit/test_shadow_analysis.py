import json

from churn.deploy import shadow_analysis as sa
from churn.deploy.common import EXIT_FAIL, EXIT_INCONCLUSIVE, EXIT_PASS

from .fakes import FakeClock, FakeProm

ARGS = [
    "--namespace",
    "churn-serving",
    "--champion",
    "churn-lgbm",
    "--shadow",
    "churn-lgbm-shadow",
    "--window",
    "2h",
    "--min-rank-corr",
    "0.85",
    "--min-tier-agreement",
    "0.90",
    "--max-p99-ms",
    "150",
    "--max-error-rate",
    "0.001",
]


def snap(**overrides):
    base = {
        "champion_requests": 10000.0,
        "shadow_requests": 9990.0,
        "error_rate": 0.0,
        "p99_ms": 90.0,
        "pairs": 9000.0,
        "tier_agreement": 0.95,
        "rank_corr": 0.93,
    }
    base.update(overrides)
    return base


def args(*extra):
    return sa.build_parser().parse_args([*ARGS, *extra])


def test_pass():
    code, checks = sa.evaluate(snap(), args())
    assert code == EXIT_PASS and all(c["ok"] for c in checks)


def test_breaches():
    for field, value, name in [
        ("rank_corr", 0.80, "rank_corr"),
        ("tier_agreement", 0.85, "tier_agreement"),
        ("p99_ms", 200.0, "p99_ms"),
        ("error_rate", 0.01, "error_rate"),
        ("shadow_requests", 100.0, "mirror_ratio"),
    ]:
        code, checks = sa.evaluate(snap(**{field: value}), args())
        assert code == EXIT_FAIL, field
        assert [c["check"] for c in checks if c["ok"] is False] == [name]


def test_inconclusive_without_pairs_or_metrics():
    assert sa.evaluate(snap(pairs=10.0), args())[0] == EXIT_INCONCLUSIVE
    assert sa.evaluate(snap(rank_corr=None), args())[0] == EXIT_INCONCLUSIVE


def test_collect_and_main_with_prometheus(tmp_path):
    prom = FakeProm(
        scalars=[
            (r"churn_shadow_rank_corr", 0.91),
            (r'tier_agree="true"', 9300.0),
            (r"churn_shadow_pairs_total", 9800.0),
            (r"histogram_quantile", 88.0),
            (r"churn-lgbm-shadow-transformer.*response_code", 2.0),
            (r"churn-lgbm-shadow-transformer", 9900.0),
            (r"churn-lgbm-transformer", 10000.0),
        ]
    )
    clock = FakeClock()
    summary = tmp_path / "summary.md"
    code = sa.main(
        [
            *ARGS,
            "--prometheus-url",
            "https://amw.example",
            "--window",
            "10m",
            "--interval",
            "5m",
            "--summary",
            str(summary),
        ],
        prom=prom,
        clock=clock,
        sleep=clock.sleep,
    )
    assert code == EXIT_PASS
    assert clock.sleeps == [300, 300]
    assert "PROMOTE" in summary.read_text()


def test_input_json_and_missing_url(tmp_path):
    path = tmp_path / "snap.json"
    path.write_text(json.dumps(snap(rank_corr=0.5)))
    assert sa.main([*ARGS, "--input-json", str(path), "--summary", str(tmp_path / "s")]) == 1
    assert sa.main([*ARGS, "--summary", str(tmp_path / "s")]) == EXIT_INCONCLUSIVE


def test_lookback_evaluates_once_over_seven_days(tmp_path):
    prom = FakeProm(
        scalars=[
            (r"churn_shadow_rank_corr", 0.91),
            (r'tier_agree="true"', 9300.0),
            (r"churn_shadow_pairs_total", 9800.0),
            (r"histogram_quantile", 88.0),
            (r"churn-lgbm-shadow-transformer.*response_code", 2.0),
            (r"churn-lgbm-shadow-transformer", 9900.0),
            (r"churn-lgbm-transformer", 10000.0),
        ]
    )
    clock = FakeClock()
    code = sa.main(
        [
            *ARGS,
            "--prometheus-url",
            "https://amw.example",
            "--lookback",
            "7d",
            "--summary",
            str(tmp_path / "s.md"),
        ],
        prom=prom,
        clock=clock,
        sleep=clock.sleep,
    )
    assert code == EXIT_PASS
    assert clock.sleeps == []  # no polling: the soak already elapsed
    assert all("[604800s]" in q for q in prom.queries)
