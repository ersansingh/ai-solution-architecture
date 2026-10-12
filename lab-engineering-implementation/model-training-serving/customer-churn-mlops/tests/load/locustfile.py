"""Load test for the M6 exit criterion: p99 < 150 ms at 2x expected peak (OD-3: 50 RPS -> 100 RPS).

  CUSTOMER_IDS=100001,100002,... API_KEY=<key> \
  locust -f tests/load/locustfile.py --host https://<api-id>.execute-api.<region>.amazonaws.com/prod \
         --users 200 --spawn-rate 20 --run-time 15m --headless --csv load-report
"""
import os
import random

from locust import HttpUser, between, task

IDS = [i for i in os.environ.get("CUSTOMER_IDS", "100001").split(",") if i]
HEADERS = {"x-api-key": os.environ.get("API_KEY", ""), "content-type": "application/json"}


class SupportAgent(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(9)
    def score(self):
        self.client.post("/v1/predict", json={"customer_id": random.choice(IDS)}, headers=HEADERS, name="predict")

    @task(1)
    def what_if(self):
        self.client.post("/v1/predict", headers=HEADERS, name="predict-what-if",
                         json={"customer_id": random.choice(IDS), "overrides": {"contract_type": "Two Year"}})
