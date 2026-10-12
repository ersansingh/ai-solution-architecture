import pytest
from fastapi.testclient import TestClient

from app.backends import ModelUnavailable, ServingConfig, UnknownCustomer, parse_probabilities, to_csv
from app.main import create_app
from app.settings import Settings
from churn import config


class FakeFeatures:
    def get(self, customer_id):
        if customer_id == "missing":
            raise UnknownCustomer(customer_id)
        record = {**{c: 1.0 for c in config.numeric_columns()}, **{c: "Yes" for c in config.categorical_columns()}}
        record["age"] = 40.0
        return record


class FakeModel:
    def __init__(self, probability=0.9, fail=False):
        self.probability, self.fail, self.calls = probability, fail, []

    def predict(self, rows, inference_id=None):
        if self.fail:
            raise ModelUnavailable("down")
        self.calls.append((rows, inference_id))
        return [self.probability]


class FakeServing:
    def current(self):
        return {"endpoint_name": "e", "threshold": 0.8, "model_version": "7", "source": "test"}


def client(model=None):
    app = create_app(Settings(), FakeFeatures(), model or FakeModel(), FakeServing())
    return TestClient(app)


def test_predict_applies_threshold_and_orders_features():
    model = FakeModel(0.85)
    with client(model) as c:
        response = c.post("/v1/predict", json={"customer_id": "100042", "overrides": {"satisfaction_score": 2}})
    assert response.status_code == 200
    body = response.json()
    assert body["churn_flag"] == 1 and body["threshold"] == 0.8 and body["model_version"] == "7"
    rows, inference_id = model.calls[0]
    columns = config.model_input_columns()
    assert len(rows[0]) == len(columns)
    sent = dict(zip(columns, rows[0]))
    assert sent["satisfaction_score"] == 2
    # engineered features are recomputed from the override: 2*1 + 1 + (10 - 2)
    assert sent["customer_risk_score"] == 11
    assert inference_id.startswith("100042:")


@pytest.mark.parametrize("payload,status", [
    ({"customer_id": "missing"}, 404),
    ({"customer_id": ""}, 400),
    ({"customer_id": "bad id!"}, 400),
    ({"customer_id": "1", "overrides": {"not_a_feature": 1}}, 400),
])
def test_error_codes(payload, status):
    with client() as c:
        assert c.post("/v1/predict", json=payload).status_code == status


def test_model_unavailable_is_503():
    with client(FakeModel(fail=True)) as c:
        assert c.post("/v1/predict", json={"customer_id": "1"}).status_code == 503


def test_health_and_readiness():
    with client() as c:
        assert c.get("/healthz").json() == {"status": "ok"}
        assert c.get("/readyz").json()["model_version"] == "7"


def test_csv_helpers_quote_and_blank_missing():
    assert to_csv([[1.0, None, "Bank Transfer", "a,b"]]) == '1.0,,Bank Transfer,"a,b"\n'
    assert parse_probabilities("0.1\n0.9\n") == [0.1, 0.9]


def test_serving_config_falls_back_to_defaults_when_ssm_fails():
    class BrokenSSM:
        def get_parameter(self, Name):
            raise RuntimeError("no ssm")

    serving = ServingConfig(Settings(), BrokenSSM())
    assert serving.current()["source"] == "defaults"


def test_metrics_payload_has_percentile_values():
    with client() as c:
        c.post("/v1/predict", json={"customer_id": "1"})
        publisher = c.app.state.metrics
        snap = publisher.snapshot_and_reset()
    data = {d["MetricName"]: d for d in publisher.metric_data(snap)}
    assert data["Predictions"]["Value"] == 1.0
    assert data["MeanPredictedChurnRate"]["Value"] == 0.9
    assert sum(data["EndToEndLatency"]["Counts"]) == 1
