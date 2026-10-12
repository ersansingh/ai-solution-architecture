# customer-churn-mlops

TeleConnect customer churn prediction on AWS. This project implements [`../engineering-implementation-plan.md`](../engineering-implementation-plan.md):

* **SageMaker** handles training, the Model Registry, the Pipeline, Batch Transform and Model Monitor.
* **EKS** hosts the real-time API.
* **Terraform** provisions all infrastructure.
* **LocalStack in Docker** runs the local test stack.

```text
Client ─► API Gateway (REST, API key, throttling, validation) ─► VPC Link ─► internal NLB
       ─► EKS: churn-api pods (FastAPI, ≥3 replicas over 3 AZs, HPA, PDB, IRSA)
            ├─► SageMaker Feature Store online store  (GetRecord by customer_id)
            ├─► SageMaker endpoint customer-churn-prod (PipelineModel: sklearn preprocessor → XGBoost,
            │     ≥2 instances, auto scaling, data capture, blue/green canary with alarm rollback)
            └─► SSM serving config (threshold, model version)  ◄── deploy state machine

S3 _MANIFEST.json / monthly cron ─► EventBridge ─► SageMaker Pipeline CustomerChurnPipeline
   Preprocess → IngestFeatures → DataQualityBaseline → TrainXGBoost (Debugger) → Evaluate
   → GateKPIs → Clarify (SHAP, bias) → RegisterModel (PendingManualApproval) | FailOnGate
Approval ─► EventBridge ─► Step Functions: staging (rolling) → smoke test → prod (blue/green) → SNS
```

The plan routed the API through Lambda. This implementation uses **EKS** instead, behind the same API Gateway. See [docs/architecture.md](docs/architecture.md) for the full set of decisions.

## Repository layout

| Path | What |
|---|---|
| `config/` | `features.yaml` holds the feature contract, shared by Python, Terraform and the API. Also here: `quality_gates.yaml`, `best_hparams.json` and `project.yaml` |
| `src/churn/` | Feature engineering, the preprocessor, evaluation, Feature Store helpers, the synthetic data generator |
| `src/churn/jobs/` | SageMaker Processing entry points (`preprocess`, `ingest_features`, `evaluate`) and `local_train` |
| `src/churn/experiments/` | M3 multi-model training with Experiments, M4 tuning |
| `pipelines/pipeline.py` | SageMaker Pipeline definition, with upsert and start |
| `deployment/` | Deploy Lambdas, Step Functions ASL, Batch Transform, Model Monitor, ground-truth merge |
| `services/churn-api/` | Real-time API (FastAPI) that runs on EKS |
| `services/model-server/` | Local stand-in for the SageMaker endpoint, using the same `/ping` and `/invocations` contract |
| `containers/lightgbm/` | LightGBM bring-your-own-container training image |
| `deploy/helm/churn-api/` | Helm chart: Deployment, HPA, PDB, TargetGroupBinding, IRSA service account |
| `infra/terraform/` | Modules (network, data_lake, ecr, eks, api, sagemaker, deploy, events, monitoring, github_oidc) and the `envs/aws` and `envs/local` environments |
| `local/` | `docker-compose.yml` (LocalStack + Terraform + trainer + seed + model-server + churn-api + tests) |
| `tests/unit`, `tests/integration`, `tests/load` | pytest unit tests; integration tests run in the Docker test container; Locust load test |

## Local development

### Unit tests (no AWS, no Docker)

```bash
make venv && make test          # 35 tests: features, preprocessing, gates, API, model server, lambdas
make train-local ROWS=200000    # generate → preprocess → train → evaluate; prints metrics + gate report
```

On the synthetic data, a 200k-row local run gives these test-split results. The threshold is selected on the validation split.

| Metric | Value | Gate |
|---|---|---|
| AUC | 0.983 | > 0.90 |
| Precision | 0.871 | > 0.85 |
| Recall | 0.817 | > 0.80 |
| Accuracy | 0.945 | ≥ 0.90 (not blocking) |

### Local stack (LocalStack Community in Docker)

```bash
make local-up       # localstack → terraform apply envs/local → train → seed → model-server → churn-api
make local-test     # pytest tests/integration inside the Docker test container
curl -s localhost:8080/v1/predict -H 'content-type: application/json' -d '{"customer_id":"<id>"}'
make local-down
```

LocalStack Community doesn't emulate SageMaker, EKS, Feature Store or API Gateway VPC links, so the local stack stands in for them:

| AWS | Local |
|---|---|
| SageMaker endpoint (PipelineModel) | `model-server`, which runs the same preprocessor handlers and XGBoost booster |
| Feature Store online store | DynamoDB table in LocalStack (`FEATURE_BACKEND=dynamodb`) |
| SageMaker Pipeline target | SQS queue; the integration test checks that one data drop produces exactly one trigger |
| EKS | The `churn-api` container. To exercise the Helm chart, run `make k3d-up k3d-deploy` instead |

These pieces run in LocalStack using the **same Terraform modules** as AWS: S3 (KMS, versioning, EventBridge notifications), EventBridge rules, SNS, CloudWatch alarms and SSM.

## Deploying to AWS

1. **Infrastructure.**
   ```bash
   cd infra/terraform/envs/aws
   cp terraform.tfvars.example terraform.tfvars
   cp backend.hcl.example backend.hcl
   terraform init -backend-config=backend.hcl && terraform apply
   ```
   This creates the VPC with endpoints, the KMS-encrypted data lake, ECR, the EKS cluster (LB controller, metrics-server, IRSA), the API Gateway, NLB and VPC link, the SageMaker role, Feature Group, Model Package Group, Athena and Studio, the deploy state machine and Lambdas, the EventBridge triggers, and the alarms, dashboard, SNS and budget.
2. **Configuration.** Set `CHURN_BUCKET`, `CHURN_REGION` and `CHURN_SAGEMAKER_ROLE_ARN` from the Terraform outputs. They override `config/project.yaml`.
3. **Data.** Run `python -m churn.data.generate_synthetic --rows 2500000 --out data`, then `aws s3 sync data/raw-data s3://$CHURN_BUCKET/raw-data`. Upload `_MANIFEST.json` last; it starts the pipeline.
4. **Experiments (M3–M4).**
   ```bash
   python -m churn.experiments.train_models --data s3://$CHURN_BUCKET/training/<execution-id> --lightgbm-image <ecr>:<tag>
   python -m churn.experiments.tune --data ...
   ```
   Tuning writes the winning settings to `config/best_hparams.json`.
5. **Pipeline.** Run `make pipeline-start`, or merge to `main` and let `churn-train.yml` do it. Approve the new version in the Model Registry; the deploy state machine then promotes it from staging to production.
6. **API.** Run `make api-push api-deploy`, or let `churn-api-deploy.yml` do it. Get the API key with `aws apigateway get-api-key --api-key <id> --include-value`.
7. **Batch, monitoring, drift.**
   * `make batch` scores 5M customers.
   * `make monitoring` creates the Model Monitor schedules.
   * `scripts/simulate_drift.py` covers acceptance test AT-8.
   * `deployment/ground_truth.py` merges churn labels once they arrive (about 90 days later).
8. **Teardown.** Run `make teardown ARGS=--yes`, then `terraform destroy`.

CI/CD details are in [docs/cicd.md](docs/cicd.md). Runbooks are in [docs/runbooks/](docs/runbooks/).
