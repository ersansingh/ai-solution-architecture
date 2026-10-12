"""Test doubles for the Prometheus client and wall clock."""

import re


class FakeProm:
    """Answers PromQL by regex -> value (scalar) or {le: value} (histogram)."""

    def __init__(self, scalars=None, histograms=None):
        self.scalars = scalars or []
        self.histograms = histograms or []
        self.queries = []

    def scalar(self, promql):
        self.queries.append(promql)
        for pattern, value in self.scalars:
            if re.search(pattern, promql):
                return value
        return None

    def histogram(self, promql):
        self.queries.append(promql)
        for pattern, value in self.histograms:
            if re.search(pattern, promql):
                return value
        return {}


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds
