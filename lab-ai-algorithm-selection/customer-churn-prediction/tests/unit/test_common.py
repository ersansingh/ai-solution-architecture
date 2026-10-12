import io
import json
import math

import pytest

from churn.deploy import common


def test_parse_duration():
    assert common.parse_duration("30m") == 1800
    assert common.parse_duration("2h") == 7200
    assert common.parse_duration("45s") == 45
    with pytest.raises(ValueError):
        common.parse_duration("30 minutes")


def test_promql_duration_floor():
    assert common.promql_duration(10) == "60s"
    assert common.promql_duration(600) == "600s"


def test_psi_identical_and_shifted():
    assert common.psi([10, 20, 30], [10, 20, 30]) == pytest.approx(0.0)
    assert common.psi([50, 30, 20], [10, 30, 60]) > 0.25
    with pytest.raises(ValueError):
        common.psi([1, 2], [1])
    with pytest.raises(ValueError):
        common.psi([0, 0], [1, 1])


def test_cumulative_to_bins():
    assert common.cumulative_to_bins({0.5: 3.0, 0.1: 1.0, math.inf: 10.0}) == [1.0, 2.0, 7.0]


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_returning(payload, seen):
    def opener(req, timeout):
        seen.append(req)
        return FakeResponse(json.dumps(payload).encode())

    return opener


def test_prometheus_client_scalar_and_histogram():
    seen = []
    client = common.PrometheusClient(
        "https://amw.example/",
        token_provider=lambda: "tok",
        opener=opener_returning(
            {
                "status": "success",
                "data": {
                    "result": [
                        {"metric": {"le": "0.5"}, "value": [0, "4"]},
                        {"metric": {"le": "+Inf"}, "value": [0, "9"]},
                        {"metric": {}, "value": [0, "1"]},
                    ]
                },
            },
            seen,
        ),
    )
    assert client.histogram("q") == {0.5: 4.0, math.inf: 9.0}
    assert client.scalar("q") == 4.0
    assert seen[0].get_header("Authorization") == "Bearer tok"
    assert seen[0].full_url.startswith("https://amw.example/api/v1/query?query=q")


def test_prometheus_client_empty_nan_and_error():
    empty = common.PrometheusClient(
        "https://x",
        token_provider=lambda: None,
        opener=opener_returning({"status": "success", "data": {"result": []}}, []),
    )
    assert empty.scalar("q") is None
    nan = common.PrometheusClient(
        "https://x",
        token_provider=lambda: None,
        opener=opener_returning(
            {"status": "success", "data": {"result": [{"metric": {}, "value": [0, "NaN"]}]}}, []
        ),
    )
    assert nan.scalar("q") is None
    bad = common.PrometheusClient(
        "https://x",
        token_provider=lambda: None,
        opener=opener_returning({"status": "error", "error": "boom"}, []),
    )
    with pytest.raises(RuntimeError):
        bad.query("q")
    with pytest.raises(ValueError):
        common.PrometheusClient("file:///etc/passwd")


def test_bearer_token_from_env(monkeypatch):
    monkeypatch.setenv("PROMETHEUS_TOKEN", "abc")
    assert common.bearer_token() == "abc"


def test_append_file(tmp_path):
    target = tmp_path / "out.md"
    common.append_file(str(target), "a")
    common.append_file(str(target), "b")
    common.append_file(None, "ignored")
    assert target.read_text() == "ab"
