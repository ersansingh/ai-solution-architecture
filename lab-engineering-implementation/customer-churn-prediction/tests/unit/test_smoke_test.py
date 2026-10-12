import io
import json
import urllib.error

from churn.deploy import smoke_test as st

GOOD = {
    "probability": 0.42,
    "tier": "B",
    "reason_codes": ["BILL_SHOCK"],
    "model_version": "12",
    "score_ts": "2026-10-10T04:30:00Z",
    "freshness": "fresh",
}


class Resp(io.BytesIO):
    def __init__(self, body, status=200, server_ms="12.5"):
        super().__init__(json.dumps(body).encode())
        self.status = status
        self.headers = {} if server_ms is None else {st.SERVER_TIMING_HEADER: server_ms}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def ids_file(tmp_path):
    path = tmp_path / "ids.txt"
    path.write_text("# comment\nabc\ndef\n")
    return str(path)


def ticking_clock(step_ms):
    state = {"t": 0.0}

    def clock():
        state["t"] += step_ms / 1000.0
        return state["t"]

    return clock


def test_validate_body():
    assert st.validate_body(GOOD) is None
    assert "probability" in st.validate_body({**GOOD, "probability": 1.5})
    assert "tier" in st.validate_body({**GOOD, "tier": "Z"})
    assert "reason_codes" in st.validate_body({**GOOD, "reason_codes": list("abcdef")})
    assert "model_version" in st.validate_body({**GOOD, "model_version": ""})


def test_p99():
    assert st.p99([float(i) for i in range(1, 101)]) == 99.0
    assert st.p99([5.0]) == 5.0


def test_main_passes(tmp_path):
    seen = []

    def opener(req, timeout):
        seen.append(req)
        return Resp(GOOD)

    code = st.main(
        [
            "--endpoint",
            "https://apim.internal/churn/v1/",
            "--samples",
            "4",
            "--max-server-p99-ms",
            "50",
            "--ids-file",
            ids_file(tmp_path),
        ],
        opener=opener,
        clock=ticking_clock(10),
        token="tok",
    )
    assert code == 0
    assert [r.full_url for r in seen[:2]] == [
        "https://apim.internal/churn/v1/customers/abc/score",
        "https://apim.internal/churn/v1/customers/def/score",
    ]
    assert seen[0].get_header("Authorization") == "Bearer tok"


def test_main_fails_on_client_latency(tmp_path):
    code = st.main(
        [
            "--endpoint",
            "https://a/churn/v1",
            "--samples",
            "3",
            "--max-server-p99-ms",
            "50",
            "--ids-file",
            ids_file(tmp_path),
        ],
        opener=lambda req, timeout: Resp(GOOD),
        clock=ticking_clock(400),
        token=None,
    )
    assert code == 1


def test_main_fails_on_errors(tmp_path):
    responses = iter([Resp(GOOD), Resp(GOOD, status=503), Resp({**GOOD, "tier": "?"})])

    def opener(req, timeout):
        r = next(responses, None)
        if r is None:
            raise urllib.error.URLError("down")
        return r

    code = st.main(
        [
            "--endpoint",
            "https://a/churn/v1",
            "--samples",
            "4",
            "--max-server-p99-ms",
            "50",
            "--ids-file",
            ids_file(tmp_path),
        ],
        opener=opener,
        clock=ticking_clock(1),
        token=None,
    )
    assert code == 1


def test_main_rejects_bad_input(tmp_path, monkeypatch):
    monkeypatch.setenv("CHURN_API_TOKEN", "t")
    assert (
        st.main(
            [
                "--endpoint",
                "http://plain",
                "--max-server-p99-ms",
                "50",
                "--ids-file",
                ids_file(tmp_path),
            ]
        )
        == 1
    )
    assert st.main(["--endpoint", "https://a", "--samples", "0", "--max-server-p99-ms", "50"]) == 1
    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing\n")
    assert (
        st.main(["--endpoint", "https://a", "--max-server-p99-ms", "50", "--ids-file", str(empty)])
        == 1
    )


def test_get_token(monkeypatch):
    monkeypatch.setenv("CHURN_API_TOKEN", "abc")
    assert st.get_token("api://churn/.default") == "abc"
    monkeypatch.delenv("CHURN_API_TOKEN")
    assert st.get_token(None) is None


def argv(tmp_path, samples="4"):
    return [
        "--endpoint",
        "https://apim.internal/churn/v1",
        "--samples",
        samples,
        "--max-server-p99-ms",
        "50",
        "--ids-file",
        ids_file(tmp_path),
    ]


def test_apim_latency_above_server_slo_passes_when_server_time_is_fast(tmp_path):
    # 120 ms through APIM is fine; the 50 ms SLO is judged on the server header
    code = st.main(
        argv(tmp_path),
        opener=lambda req, timeout: Resp({**GOOD, "freshness": "batch"}, server_ms="18"),
        clock=ticking_clock(120),
        token=None,
    )
    assert code == 0


def test_server_side_slo_breach_fails_per_path(tmp_path):
    slow_pre = st.main(
        argv(tmp_path),
        opener=lambda req, timeout: Resp({**GOOD, "freshness": "batch"}, server_ms="75"),
        clock=ticking_clock(5),
        token=None,
    )
    assert slow_pre == 1
    # 75 ms on the rescoring path is within the 150 ms rescoring SLO
    rescore = st.main(
        argv(tmp_path),
        opener=lambda req, timeout: Resp({**GOOD, "freshness": "fresh"}, server_ms="75"),
        clock=ticking_clock(5),
        token=None,
    )
    assert rescore == 0


def test_missing_server_timing_header_fails(tmp_path):
    args = st.build_parser().parse_args(argv(tmp_path, samples="2"))
    ok, result = st.run(
        args,
        opener=lambda req, timeout: Resp(GOOD, server_ms=None),
        clock=ticking_clock(5),
    )
    assert not ok
    assert "x-churn-server-time-ms" in result["first_errors"][0]
    assert result["checks"]["server_timing_observed"] is False


def test_server_time_parsing():
    assert st.server_time_ms({"h": " 3.5 "}, "h") == 3.5
    assert st.server_time_ms({"h": "abc"}, "h") is None
    assert st.server_time_ms({"h": "-1"}, "h") is None
    assert st.server_time_ms(None, "h") is None
