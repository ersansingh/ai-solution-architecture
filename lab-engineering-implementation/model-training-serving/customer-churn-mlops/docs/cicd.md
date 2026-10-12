# CI/CD (Phase 10)

| Workflow (repo root `.github/workflows/`) | Trigger | What it does |
|---|---|---|
| `churn-ci.yml` | PRs and pushes touching this project | flake8 and unit tests. `terraform fmt -check` and `validate` (local + aws). `helm lint` and `template`. LightGBM image build. **Local integration**: `make local-up` (LocalStack + Terraform + model-server + churn-api), then `make local-test` in the Docker test container. |
| `churn-train.yml` | Merge to `main` touching `src/`, `pipelines/` or `config/` | Assumes the OIDC role, then `pipelines/pipeline.py --upsert --start --git-sha $GITHUB_SHA` |
| `churn-api-deploy.yml` | Merge to `main` touching the API, the chart or `features.yaml` | Builds and pushes to ECR. Runs `helm upgrade --atomic`, a rolling update with `maxUnavailable=0` that rolls back automatically on failure. Then a smoke test through API Gateway. |

## Model promotion (not in GitHub)

```text
Pipeline registers vN (PendingManualApproval)
  → reviewer checks evaluation.json, Clarify SHAP and bias reports, Debugger findings → Approve
  → EventBridge "SageMaker Model Package State Change" (Approved)
  → Step Functions teleconnect-churn-deploy:
      staging: create/rolling update → wait InService → smoke test (50 golden records, p99 ≤ 150 ms, accuracy ≥ 0.8)
      → publish staging serving config
      prod: blue/green CANARY 10% (10 min bake) → 100%, AutoRollback on churn-prod-5xx-rollback / churn-prod-latency-rollback
      → re-attach auto scaling (min 2, max 6) → publish prod serving config (threshold, version) → SNS
```

## GitHub repository variables

`AWS_REGION`, `AWS_DEPLOY_ROLE_ARN`, `CHURN_BUCKET`, `SAGEMAKER_ROLE_ARN`, `EKS_CLUSTER`, `CHURN_API_ECR`, `CHURN_API_HELM_VALUES` (from `terraform output -raw churn_api_helm_values`), `API_INVOKE_URL` and `SMOKE_CUSTOMER_ID`. Secret: `CHURN_API_SMOKE_KEY`. Protect the `ml-training` and `production` environments with required reviewers.
