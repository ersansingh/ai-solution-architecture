# Churn MLOps pipeline

`churn-mlops-pipeline.yml` is the GitHub Actions workflow for CI, Terraform, continuous training (Azure ML) and progressive delivery (KServe on AKS). Copy it to `.github/workflows/` to activate it. `pipelines/aml/` holds the Azure ML CLI v2 training pipeline, components and datastores.

Job order: `changes`, `ci-quality` -> `build-and-scan` | `terraform-plan` -> `terraform-apply` | `feature-store-apply` -> `ct-train` -> `ct-evaluate` -> `register-model` -> `deploy-shadow` -> `shadow-analysis` (7 days later) -> `deploy-canary`.

## Required GitHub configuration

None of these can be created from the repository. Create them under *Settings -> Secrets and variables -> Actions* and *Settings -> Environments* before the first run. `tests/unit/test_pipeline_references.py` fails when the workflow references a secret, variable or environment that is not listed here.

### Secrets

| Secret | Used by | Value |
|---|---|---|
| `AZURE_CLIENT_ID` | every `azure/login` step, Terraform (`ARM_CLIENT_ID`) | Client ID of the Entra app or user-assigned identity with GitHub OIDC federated credentials (branch `main` plus the environments below) |
| `AZURE_TENANT_ID` | `azure/login`, Terraform, `secretproviderclass-redis.yaml` (`tenantId`) | Entra tenant ID |
| `AZURE_SUBSCRIPTION_ID` | `azure/login`, Terraform (`ARM_SUBSCRIPTION_ID`, `TF_VAR_subscription_id`) | Subscription that holds `rg-churn-prod-westeurope` |
| `TEAMS_WEBHOOK_URL` | `deploy-canary` notification | Teams incoming webhook (or a PagerDuty Events bridge) |

### Variables

| Variable | Used by | Value / source |
|---|---|---|
| `ACR_NAME` | image build/push, InferenceService image | `acr<project><env><suffix>`, from `terraform output -raw acr_login_server` without `.azurecr.io` |
| `TFSTATE_RG`, `TFSTATE_ACCOUNT` | `terraform init` backend | Resource group and storage account of the remote state |
| `LAKE_STORAGE_ACCOUNT` | Feast apply, AML datastores, model export | `terraform output -raw lake_storage_account_name` |
| `KEY_VAULT_NAME` | Feast apply (Redis secret), SecretProviderClass | `kv-<project><env><suffix>`. The name is the host part of `terraform output -raw key_vault_uri`. |
| `SERVING_IDENTITY_CLIENT_ID` | SecretProviderClass `clientID` | `terraform output -raw serving_workload_identity_client_id` |
| `AMW_PROMETHEUS_QUERY_URL` | shadow and canary analysis | Query endpoint of the Azure Monitor workspace `amw-churn-prod` |
| `ISTIO_INGRESS_GATEWAY` | `virtualservice-api.yaml` / `virtualservice-mirror.yaml` | `<namespace>/<name>` of the Istio `Gateway` on the AKS add-on internal ingress gateway that terminates TLS for `CHURN_API_INGRESS_HOST`, e.g. `aks-istio-ingress/churn-api-gateway` (platform-owned) |
| `CHURN_API_INGRESS_HOST` | same | Host that APIM's backend for the Churn API sends to the ingress gateway, e.g. `churn-scoring.internal.<domain>` |
| `CHURN_API_INTERNAL_URL` | post-promotion smoke test | Internal APIM API base incl. version, e.g. `https://apim-churn-prod-<suffix>.azure-api.net/churn/v1` |
| `CHURN_API_SCOPE` | smoke test token (`azure-identity`) | Entra app scope of the Churn API, e.g. `api://churn-scoring/.default`. The OIDC principal needs the `churn.score.read` app role. |

### Environments

| Environment | Used by | Protection rules |
|---|---|---|
| `build` | `build-and-scan` | None (scopes the OIDC subject for ACR push) |
| `infra-prod` | `terraform-apply` | Required reviewers: platform + security |
| `staging` | `deploy-shadow` | Optional reviewers |
| `shadow-soak` | `shadow-analysis` | **Wait timer 10080 minutes (7 days)**. The job checks the shadow's age and fails if the timer is missing. |
| `production` | `deploy-canary` | Required reviewers: Model Risk Owner (and ML lead / Customer Success owner) |

Each environment needs a federated credential on `AZURE_CLIENT_ID` (`repo:<org>/<repo>:environment:<name>`).

## Azure prerequisites outside this folder

The workflow does not create these, and terraform does not create them today:

1. **Lake filesystem `models`**: add `"models"` to `var.lake_containers` (terraform). `register-model` fails with a clear error until it exists. The export does not create it, because a container created out of band would later block `terraform apply`.
2. **Key Vault secret `redis-connection-string`**: value `<redis-hostname>:6380,ssl=true,password=<access key>`. This is Feast's Redis format. The cache is clustered, so the config uses `redis_type: redis_cluster`. Terraform enables Entra auth on Redis and grants `id-serving` a "Data Reader" access policy, but Feast's Redis store cannot refresh Entra tokens. Until Feast supports that, the online store uses an access-key connection string stored in Key Vault. Write it with an `azurerm_key_vault_secret` (from `azurerm_redis_cache.feast_online.primary_access_key`) or by hand.
3. **RBAC for the GitHub OIDC principal**: "Storage Blob Data Contributor" on the lake (model export, `feature_store.yaml` upload, Feast registry), "Key Vault Secrets User" on the vault (Feast apply), "AzureML Data Scientist" (or a custom role with datastore write) on `mlw-churn-prod`, and "Azure Kubernetes Service RBAC Writer" on `churn-serving`.
4. **Self-hosted runners** (`[self-hosted, linux, churn-vnet]`) inside the spoke VNet, with `az`, `kubectl`, `kubelogin`, `envsubst` and GNU `date`. The lake, Key Vault, Azure ML and AKS are reachable only through private endpoints.

## Model location (KServe)

`register-model` registers `runs:/<run>/model` in the Azure ML MLflow registry and then runs `python -m churn.deploy.export_model`. That step copies the version's artifacts (`model.bst`, `calibrator.json`, `MLmodel`, ...) to:

```
https://<LAKE_STORAGE_ACCOUNT>.blob.core.windows.net/models/<MODEL_NAME>/<version>/artifacts
```

It writes `manifest.json` (sha256 per file) last, and that file marks the export as complete. The URI is the `storageUri` of the predictor and the `STORAGE_URI` of the transformer. KServe's Azure Blob support authenticates with `DefaultAzureCredential` when `AZURE_CLIENT_ID` is present, and the workload identity webhook injects that variable (`azure.workload.identity/use: "true"`, service account `churn-kserve-sa`). The `/artifacts` suffix is required because KServe lists blobs by raw prefix, so `.../7` would also download `.../70/`.

## Feature store

`features/` is the Feast repo and the single source of truth. `features/feature_store.yaml` is used in three places:

- The `feature-store-apply` job runs `feast plan` and `feast apply` against the shared registry `https://<lake>.blob.core.windows.net/feast-offline/registry/registry.db`.
- The same job uploads a copy with the lake account substituted to `feast-offline/repo/feature_store.yaml`. That copy is the training pipeline's `feast_config` input.
- The file is baked into the transformer image through the `features` named build context (`serving/Dockerfile`).

## Shadow soak (7 days)

1. `deploy-shadow` applies the shadow InferenceService and the mirroring VirtualService.
2. It runs a 30-minute warm-up gate. A breach removes the shadow at once.
3. If the gate passes, the shadow keeps running.
4. `shadow-analysis` waits on the `shadow-soak` environment timer. A job waiting on an environment does not hold a runner, and a workflow run may last up to 35 days.
5. The job checks that the shadow is still this run's model version. A newer retrain may have superseded it, in which case this run stops without promoting.
6. It checks that the shadow has run for at least 7 days.
7. It evaluates the whole soak once (`--lookback <age>s`) and removes the shadow.
8. `deploy-canary` (production approval) follows.

Concurrency is per job, not per workflow, so the open run does not block CI on `main`.

Local equivalent of the datastore step:

```bash
LAKE_STORAGE_ACCOUNT=$(terraform -chdir=terraform output -raw lake_storage_account_name) \
AZURE_RESOURCE_GROUP=rg-churn-prod-westeurope AML_WORKSPACE=mlw-churn-prod \
bash pipelines/aml/scripts/ensure-datastores.sh
```
