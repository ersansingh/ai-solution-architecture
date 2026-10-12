# Runbook: monitoring alerts

| Alarm | Meaning | First actions |
|---|---|---|
| `churn-api-gateway-latency-p99`, `churn-api-service-latency-p99` | End-to-end p99 above 150 ms | Compare with `churn-prod-model-latency-p99`. If the model is fine, check HPA and pod CPU (`kubectl -n churn top pods`) and Feature Store throttling. If the model is slow, check endpoint CPU and instance count, and the auto-scaling activity. |
| `churn-prod-model-latency-p99` | Model above its 50 ms budget | Scale out (raise min capacity), or check for very large payloads |
| `churn-prod-endpoint-5xx-rate`, `churn-api-gateway-5xx-rate` | Errors above 2% | Endpoint CloudWatch logs (`/aws/sagemaker/Endpoints/customer-churn-prod`); churn-api logs (`event: model_unavailable`) |
| `churn-prod-endpoint-cpu` | Sustained CPU above 80% | Lower the auto-scaling target `target_invocations_per_instance`, or raise max capacity |
| `churn-drift-<feature>` | Model Monitor drift distance above 0.2 | Open the violation report under `monitoring/reports/data-quality/`. Confirm whether the change is real (pricing change, campaign) or an upstream data bug. A real shift means retraining: upload a manifest or start the pipeline. |
| `churn-prediction-distribution-high/low` | Mean predicted churn more than 5 pp from the training rate | Early warning before labels arrive. Correlate with drift alarms and business events. |
| `churn-model-quality-auc` | Ground-truth AUC below 0.88 | Model decay confirmed; retrain, and review features |
| Pipeline failed (EventBridge → SNS) | `CustomerChurnPipeline` execution failed | Check the failing step in Studio. `FailOnGate` means the KPIs weren't met, which isn't an infrastructure fault. |

**Drift simulation (AT-8).** Run `python scripts/simulate_drift.py --test-raw s3://<bucket>/training/<exec>/test_raw/test_raw.csv`. Then start the data-quality job on demand, or wait for the daily run.
