"""Per-pod CloudWatch metrics: latency percentiles, prediction distribution (plan section 6.6)."""
from __future__ import annotations

import threading
from collections import Counter
from typing import Optional

import boto3


class MetricsPublisher:
    def __init__(self, namespace: str, stage: str, interval_s: int, region: str, enabled: bool):
        self._namespace, self._interval, self._enabled = namespace, interval_s, enabled
        self._dimensions = [{"Name": "Service", "Value": "churn-api"}, {"Name": "Stage", "Value": stage}]
        self._region = region
        self._lock = threading.Lock()
        self._reset()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _reset(self):
        self._latencies: Counter = Counter()
        self._count = self._flags = self._errors = 0
        self._prob_sum = 0.0

    def record(self, latency_ms: float, probability: Optional[float] = None, flag: Optional[int] = None,
               error: bool = False):
        with self._lock:
            self._latencies[int(round(latency_ms))] += 1
            if error:
                self._errors += 1
                return
            self._count += 1
            self._prob_sum += probability or 0.0
            self._flags += flag or 0

    def snapshot_and_reset(self) -> dict:
        with self._lock:
            snap = {"latencies": dict(self._latencies), "count": self._count, "errors": self._errors,
                    "prob_sum": self._prob_sum, "flags": self._flags}
            self._reset()
        return snap

    def metric_data(self, snap: dict) -> list:
        data = []
        items = sorted(snap["latencies"].items())
        for i in range(0, len(items), 150):  # PutMetricData accepts up to 150 values per datum
            chunk = items[i:i + 150]
            data.append({"MetricName": "EndToEndLatency", "Dimensions": self._dimensions, "Unit": "Milliseconds",
                         "Values": [float(v) for v, _ in chunk], "Counts": [float(c) for _, c in chunk]})
        data.append({"MetricName": "Predictions", "Dimensions": self._dimensions, "Unit": "Count",
                     "Value": float(snap["count"])})
        data.append({"MetricName": "Errors", "Dimensions": self._dimensions, "Unit": "Count",
                     "Value": float(snap["errors"])})
        if snap["count"]:
            data.append({"MetricName": "MeanPredictedChurnRate", "Dimensions": self._dimensions, "Unit": "None",
                         "Value": snap["prob_sum"] / snap["count"]})
            data.append({"MetricName": "ChurnFlagRate", "Dimensions": self._dimensions, "Unit": "None",
                         "Value": snap["flags"] / snap["count"]})
        return data

    def flush(self):
        snap = self.snapshot_and_reset()
        if not self._enabled or (not snap["count"] and not snap["errors"]):
            return
        client = boto3.client("cloudwatch", region_name=self._region)
        data = self.metric_data(snap)
        for i in range(0, len(data), 20):
            client.put_metric_data(Namespace=self._namespace, MetricData=data[i:i + 20])

    def start(self):
        if not self._enabled:
            return

        def loop():
            while not self._stop.wait(self._interval):
                try:
                    self.flush()
                except Exception:  # noqa: BLE001 - metrics must never take the API down
                    pass

        self._thread = threading.Thread(target=loop, daemon=True, name="metrics")
        self._thread.start()

    def stop(self):
        self._stop.set()
        try:
            self.flush()
        except Exception:  # noqa: BLE001
            pass
