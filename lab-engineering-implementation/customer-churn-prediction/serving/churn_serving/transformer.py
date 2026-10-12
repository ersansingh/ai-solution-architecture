"""KServe Transformer: Feast lookup, precomputed vs rescoring path, calibration.

Request (KServe V1, mapped by APIM from ``GET /churn/v1/customers/{pseudoId}/score``
and ``POST /churn/v1/score:rescore``)::

    {"instances": [{"pseudo_customer_id": "<hmac>", "rescore": false}]}

Response per instance::

    {"probability", "tier", "reason_codes"[<=5], "model_version", "score_ts", "freshness"}

Paths (system-design.md 6.2):

* precomputed: batch score from the Feast online store when no material event
  happened since ``score_ts`` (p99 < 50 ms)
* rescoring: fresh feature vector -> Predictor (MLServer LightGBM, V2) ->
  isotonic calibration -> TreeSHAP top-5 reason codes (p99 < 150 ms)

TreeSHAP runs in-process with LightGBM's native ``pred_contrib`` on the same
``model.bst`` the predictor serves (downloaded from ``STORAGE_URI``), so no
separate explainer hop or ``shap`` dependency is needed. Only risk-increasing
drivers are returned, mapped to business reason codes; raw SHAP values never
leave the transformer.

Shadow mode (``SHADOW_MODE=true``, used by ``inferenceservice-shadow.yaml``):
always rescores and additionally scores the *same* feature vector on the
champion predictor (``CHAMPION_PREDICTOR_HOST``), exporting
``churn_shadow_pairs_total`` and ``churn_shadow_rank_corr`` for
``churn.deploy.shadow_analysis``.

Metrics carry ``isvc`` and ``revision`` (Knative ``K_REVISION``) labels so that
``churn.deploy.canary_analysis`` can compare canary and stable revisions.
"""

from __future__ import annotations

import bisect
import json
import os
import time
from collections import deque
from datetime import UTC, datetime
from typing import Any

import httpx
import lightgbm as lgb
import numpy as np
from feast import FeatureStore
from kserve import Model
from kserve.storage import Storage  # not re-exported as kserve.Storage in 0.13
from prometheus_client import Counter, Gauge, Histogram

ISVC = os.environ.get("CHURN_ISVC", "churn-lgbm")
REVISION = os.environ.get("K_REVISION", "unknown")
SHADOW_MODE = os.environ.get("SHADOW_MODE", "false").lower() == "true"
TOP_K = 5
SCORE_BUCKETS = (0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)

SCORE = Histogram(
    "churn_score",
    "Calibrated churn probability returned",
    ["isvc", "revision", "path"],
    buckets=SCORE_BUCKETS,
)
TIERS = Counter("churn_tier", "Risk tiers returned", ["isvc", "revision", "tier"])
PATHS = Counter("churn_path", "Serving path taken", ["isvc", "revision", "path"])
SHADOW_PAIRS = Counter(
    "churn_shadow_pairs", "Shadow vs champion paired scores", ["isvc", "tier_agree"]
)
SHADOW_RANK_CORR = Gauge("churn_shadow_rank_corr", "Spearman over recent pairs", ["isvc"])

ONLINE_SCORE_FEATURES = [
    "churn_score:probability",
    "churn_score:tier",
    "churn_score:reason_codes",
    "churn_score:model_version",
    "churn_score:score_ts",
    "customer_streaming:last_material_event_ts",
]


def tier_for(prob: float, cfg: dict[str, Any]) -> str:
    if prob >= cfg["tier_a_threshold"]:
        return "A"
    if prob >= cfg["tier_b_threshold"]:
        return "B"
    return "LOW"


def calibrate(raw: float, cfg: dict[str, Any]) -> float:
    """Piecewise-linear isotonic mapping from calibrator.json (x ascending)."""
    xs, ys = cfg["calibrator"]["x"], cfg["calibrator"]["y"]
    if raw <= xs[0]:
        return ys[0]
    if raw >= xs[-1]:
        return ys[-1]
    i = bisect.bisect_right(xs, raw)
    x0, x1, y0, y1 = xs[i - 1], xs[i], ys[i - 1], ys[i]
    return y0 + (y1 - y0) * (raw - x0) / (x1 - x0) if x1 > x0 else y0


def spearman(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 3:
        return None

    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=values.__getitem__)
        r = [0.0] * len(values)
        for rank, idx in enumerate(order):
            r[idx] = float(rank)
        return r

    a, b = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    n = len(pairs)
    mean = (n - 1) / 2.0
    cov = sum((x - mean) * (y - mean) for x, y in zip(a, b))
    var = sum((x - mean) ** 2 for x in a)
    return cov / var if var else None


class ChurnTransformer(Model):
    def __init__(self, name: str, predictor_host: str) -> None:
        super().__init__(name)
        self.predictor_host = predictor_host
        self.booster: lgb.Booster | None = None
        self.champion_host = os.environ.get("CHAMPION_PREDICTOR_HOST")
        self.champion_model = os.environ.get("CHAMPION_MODEL_NAME", "churn-lgbm")
        self.cfg: dict[str, Any] = {}
        self.store: FeatureStore | None = None
        self.client = httpx.AsyncClient(timeout=float(os.environ.get("HOP_TIMEOUT_S", "0.3")))
        self.pairs: deque[tuple[float, float]] = deque(maxlen=5000)

    def load(self) -> bool:
        # STORAGE_URI = https://<lake>.blob.core.windows.net/models/<name>/<ver>/artifacts
        # (churn.deploy.export_model); DefaultAzureCredential via workload identity.
        local = Storage.download(os.environ["STORAGE_URI"])
        with open(os.path.join(local, "calibrator.json")) as fh:
            self.cfg = json.load(fh)
        self.booster = lgb.Booster(model_file=os.path.join(local, "model.bst"))
        self.store = FeatureStore(repo_path=os.environ.get("FEAST_REPO_PATH", "/app/feature_repo"))
        self.ready = True
        return self.ready

    def _online(self, ids: list[str], features: list[str]) -> list[dict[str, Any]]:
        rows = [{"pseudo_customer_id": i} for i in ids]
        data = self.store.get_online_features(features=features, entity_rows=rows).to_dict()
        return [{k.split("__")[-1]: v[n] for k, v in data.items()} for n in range(len(ids))]

    async def _v2_score(self, host: str, model: str, vectors: list[list[float]]) -> list[float]:
        body = {
            "inputs": [
                {
                    "name": "input-0",
                    "shape": [len(vectors), len(vectors[0])],
                    "datatype": "FP32",
                    "data": vectors,
                }
            ]
        }
        resp = await self.client.post(f"http://{host}/v2/models/{model}/infer", json=body)
        resp.raise_for_status()
        return [float(x) for x in resp.json()["outputs"][0]["data"]]

    def _reason_codes(self, vectors: list[list[float]]) -> list[list[str]]:
        """TreeSHAP top-5 risk-increasing drivers -> reason codes."""
        contribs = self.booster.predict(np.asarray(vectors, dtype=np.float32), pred_contrib=True)
        features, mapping = self.cfg["features"], self.cfg.get("reason_codes", {})
        out = []
        for row in np.asarray(contribs)[:, :-1]:  # last column is the expected value
            codes: list[str] = []
            for idx in np.argsort(-row):
                if row[idx] <= 0 or len(codes) == TOP_K:
                    break
                code = mapping.get(features[idx], features[idx].upper())
                if code not in codes:
                    codes.append(code)
            out.append(codes)
        return out

    async def predict(self, payload: dict, headers: dict[str, str] | None = None) -> dict:
        instances = payload.get("instances") or []
        ids = [str(i["pseudo_customer_id"]) for i in instances]
        stored = self._online(ids, ONLINE_SCORE_FEATURES)
        outputs: list[dict[str, Any] | None] = [None] * len(ids)
        rescore_idx: list[int] = []
        for n, (inst, row) in enumerate(zip(instances, stored)):
            last_event, score_ts = row.get("last_material_event_ts"), row.get("score_ts")
            fresh = score_ts is not None and (last_event is None or last_event <= score_ts)
            if row.get("probability") is not None and fresh and not inst.get("rescore"):
                outputs[n] = self._respond(row, "precomputed")
            else:
                rescore_idx.append(n)
        if SHADOW_MODE:
            rescore_idx = list(range(len(ids)))

        if rescore_idx:
            feats = self._online([ids[n] for n in rescore_idx], self.cfg["feast_features"])
            vectors = [[float(r.get(f) or 0.0) for f in self.cfg["features"]] for r in feats]
            raw = await self._v2_score(self.predictor_host, self.name, vectors)
            probs = [calibrate(p, self.cfg) for p in raw]
            codes = self._reason_codes(vectors)
            if SHADOW_MODE and self.champion_host:
                await self._record_shadow(vectors, probs)
            now = datetime.now(UTC).isoformat()
            for k, n in enumerate(rescore_idx):
                row = {
                    "probability": probs[k],
                    "reason_codes": codes[k][:5],
                    "model_version": self.cfg.get("model_version", "unknown"),
                    "score_ts": now,
                }
                outputs[n] = self._respond(row, "rescore")
        return {"predictions": outputs}

    async def _record_shadow(self, vectors: list[list[float]], probs: list[float]) -> None:
        champ = [
            calibrate(p, self.cfg)
            for p in await self._v2_score(self.champion_host, self.champion_model, vectors)
        ]
        for s, c in zip(probs, champ):
            agree = tier_for(s, self.cfg) == tier_for(c, self.cfg)
            SHADOW_PAIRS.labels(ISVC, str(agree).lower()).inc()
            self.pairs.append((s, c))
        corr = spearman(list(self.pairs))
        if corr is not None:
            SHADOW_RANK_CORR.labels(ISVC).set(corr)

    def _respond(self, row: dict[str, Any], path: str) -> dict[str, Any]:
        prob = float(row["probability"])
        tier = row.get("tier") or tier_for(prob, self.cfg)
        codes = row.get("reason_codes") or []
        if isinstance(codes, str):
            codes = [c for c in codes.split(",") if c]
        SCORE.labels(ISVC, REVISION, path).observe(prob)
        TIERS.labels(ISVC, REVISION, tier).inc()
        PATHS.labels(ISVC, REVISION, path).inc()
        return {
            "probability": round(prob, 6),
            "tier": tier,
            "reason_codes": codes[:5],
            "model_version": str(row.get("model_version", "unknown")),
            "score_ts": str(row.get("score_ts") or time.time()),
            "freshness": "fresh" if path == "rescore" else "batch",
        }
