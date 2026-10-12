# Engineering Implementation Plan: TeleConnect Customer Churn Prediction on AWS SageMaker

> **Problem statement:** [`customer-churn-predition.md`](customer-churn-predition.md)
> **Implementation guides:** [`implementation-guide/`](implementation-guide/) (Phases 1–11)
> **Sample data:** [`training-samples/`](training-samples/)
> **Plan date:** 2026-10-10

---

## 1. Purpose and Scope

This plan turns the TeleConnect churn problem statement and the 11 phase guides into one engineering build plan. It defines:

* the target architecture and the key design decisions behind it
* the repository, naming, and S3 conventions every phase uses
* milestones, tasks, owners, estimates, and exit criteria
* the gaps and errors in the phase guides and sample data that have to be fixed before the KPIs are achievable
* the test, acceptance, security, and cost controls for the solution

**In scope:** everything in Lab Parts 1–13, the 12 expected deliverables, Phase 10 CI/CD, and the Phase 11 acceptance tests.
**Out of scope:** streaming feature ingestion (Kinesis/MSK), multi-account deployment, and QuickSight dashboards. These are Phase 11 optional challenges and are listed under [§13](#13-optional-extensions-backlog).

---

## 2. Requirements and Design Response

| # | Requirement (source) | Target | Design response |
|---|---|---|---|
| R1 | ROC AUC | > 0.90 | XGBoost with Bayesian HPO on `validation:auc`; quality gate in the pipeline |
| R2 | Precision | > 85% | Decision threshold tuned on the validation set (not a fixed 0.5); gate checked on the test set |
| R3 | Recall | > 80% | `scale_pos_weight ≈ 4.5` (82/18 class ratio); threshold chosen to meet recall first, then maximise precision |
| R4 | Batch scoring | 5M customers < 30 min | Batch Transform, input sharded into ≥ 40 files, `MultiRecord` + `Line` split, 4+ instances, sized by load test |
| R5 | Real-time latency | < 150 ms | Measured end to end at API Gateway (p99). Latency budget in [§6.3](#63-real-time-latency-budget) |
| R6 | Availability | 99.9% | ≥ 2 endpoint instances (spread across AZs), auto scaling, Lambda provisioned concurrency, blue/green deployment with auto rollback |
| R7 | Monthly retraining | Automated | EventBridge schedule `cron(0 2 ? * SUN#1 *)` plus an S3 manifest-file trigger, both targeting the SageMaker Pipeline |
| R8 | Track all experiments | — | SageMaker Experiments runs (or the managed MLflow tracking server on new Studio domains) for every training and tuning job |
| R9 | Version every model | — | Model Package Group `Customer-Churn-Models` with metrics, dataset version, Git SHA, and approval status |
| R10 | CI/CD | — | GitHub Actions (OIDC to AWS) for CI and pipeline upsert; Step Functions for staging → production promotion |
| R11 | Explainability and bias | SHAP report | Clarify SHAP (global + local) and pre/post-training bias on gender, age band, and region |
| R12 | Monitoring | Drift, quality, latency, errors | Data capture, Model Monitor (data quality + model quality), CloudWatch dashboard and alarms, SNS |

---

## 3. Gaps and Corrections to the Inputs

These issues were found while reviewing the guides and the sample data. Each one is assigned to a milestone.

### 3.1 Data

| ID | Finding | Impact | Resolution | Milestone |
|---|---|---|---|---|
| D1 | The sample data has **200 rows, 35.5% churn, and no missing values or duplicates**. The spec says 2.5M rows, 18% churn, missing values, and 48 features. | EDA, imputation, and imbalance handling can't be exercised. The KPIs can't be measured meaningfully on a 30-row test split. | Build `src/data/generate_synthetic.py`. It scales the sample schema to 2.5M training customers and a 5M scoring population, sets churn to 18%, injects about 3–5% nulls and 0.5% duplicates, and plants a learnable churn signal driven by contract, satisfaction, complaints, and tenure. | M0 |
| D2 | **Usage Growth Rate** and **Payment Delay Score** are required features (Lab Part 3), but the source data has no time series or payment dates. Phase 3 replaces them with `payment_risk` and `engagement_score`. | 2 of the 7 required features can't be built. | The generator adds `data_usage_gb_prev_3m` and `avg_days_past_due`. Compute `usage_growth_rate` and `payment_delay_score` from these, and keep the Phase 3 features as well. | M0, M2 |
| D3 | The raw schema has about 23 source columns, against "48 features" in the spec. | The spec's feature count doesn't match the data. | Treat 48 as the post-engineering, post-encoding width. Record the final feature list in `config/features.yaml`. | M2 |

### 3.2 Implementation guides

| ID | Guide | Finding | Resolution | Milestone |
|---|---|---|---|---|
| G1 | Phase 3, Tasks 8–9 | Scaling (Task 8) runs **before** feature engineering (Task 9), so CLV and the ratio features are calculated on standardised (and sometimes negative) values. | Order: clean → engineer features on raw values → split → fit encoders and scalers on **train only**. | M2 |
| G2 | Phase 3, Task 8 | `StandardScaler.fit_transform` runs on the full dataset before the split, which leaks test statistics into training. | Fit the preprocessor on train only and save it as `preprocessor.joblib`. | M2 |
| G3 | Phase 3, Task 7 | `pd.get_dummies` at training time can't be reproduced at inference, so training and serving drift apart. | Use a `ColumnTransformer` saved with the model and served as the first container of a SageMaker **PipelineModel** (preprocessor → XGBoost). | M2, M6 |
| G4 | Phase 4 | The built-in XGBoost and Linear Learner algorithms need CSV with **the label in the first column and no header**. The guide's CSVs have headers, with `churn` in the middle. | Processing writes `training/{train,validation}/` as headerless, label-first files. `test/` is kept with headers for evaluation. | M2 |
| G5 | Phase 4, Task 7 | Linear Learner is trained without a validation channel and without imbalance handling. | Add a validation channel, `positive_example_weight_mult="balanced"`, `binary_classifier_model_selection_criteria="precision_at_target_recall"`, and `target_recall=0.8`. | M3 |
| G6 | Phase 4, Task 9 | LightGBM is optional in the guide, but the problem statement requires it (custom container). | Build a bring-your-own-container (BYOC) LightGBM image and push it to ECR (`containers/lightgbm/`). It's mandatory in this plan. | M3 |
| G7 | Phase 5 | The tuning ranges leave out **regularization**, which Lab Part 5 requires. | Add `alpha` (L1, 0–10) and `lambda` (L2, 0–10). Use Bayesian strategy and `early_stopping_type="Auto"`. | M4 |
| G8 | Phase 7 | Debugger's "gradient explosion" rule doesn't apply to gradient-boosted trees. | For XGBoost, use `loss_not_decreasing`, `overtraining`, `overfit`, `tree_depth`, `class_imbalance`, and `feature_importance_overweight`. Detect dead features as features with zero gain importance. Document why gradient rules don't apply to trees. | M5 |
| G9 | Phase 8, Task 8 | The Lambda example payload sends 3 fields (with `monthly_charge` instead of `monthly_charges`), but the model needs every feature. | The API takes `customer_id` and optional overrides. Lambda reads the record from the **Feature Store online store**, then invokes the endpoint. | M6 |
| G10 | Phase 8, Task 13 | Batch Transform scores `train_path`, a labeled training file. | Score a label-free 5M scoring snapshot from `predictions/input/`. Use `input_filter`, `join_source="Input"`, and `output_filter` so `customer_id` is carried through to the output. | M6 |
| G11 | Phase 8, Task 11 | Auto scaling starts at a minimum of 1 instance, which can't meet 99.9% availability. | Set a minimum of 2 instances and a maximum of 6. Use target tracking on `SageMakerVariantInvocationsPerInstance`, with the target value taken from the load test. | M6 |
| G12 | Phase 9 | Model-quality monitoring is described without ground truth. Churn labels only arrive about 90 days after prediction. | Add a monthly ground-truth merge job that writes labels to `monitoring/ground-truth/`. Until labels arrive, use **prediction-distribution drift** (mean predicted churn rate as a custom CloudWatch metric) as the early warning. | M7 |
| G13 | Phase 9 | The alarm threshold says "Latency > 150 ms", but the CloudWatch `ModelLatency` metric is reported in **microseconds**. | Alarm on API Gateway `Latency` p99 > 150 ms (end to end) and on `ModelLatency` p99 > 50,000 µs (model budget). | M7 |
| G14 | Phases 1, 9, 11 | The S3 layouts don't match: `pipeline/` vs `pipelines/`, and Phase 9 hard-codes `s3://teleconnect-churn/`. | Use the single layout in [§5.2](#52-s3-data-lake-layout) and read it from `config/project.yaml`. | M0 |
| G15 | Lab Part 9 vs Phase 10 | The problem statement asks for a **rolling** deployment, and Phase 10 asks for **blue/green**. | Production promotion uses blue/green **canary** (10% → 100%) with alarm-based auto rollback. A `RollingUpdatePolicy` update is shown once in staging to cover Part 9. | M6, M9 |
| G16 | Phase 10, Task 4 | There's an accuracy gate of ≥ 90%, but with 18% churn, predicting "no churn" for everyone already scores 82%. | Keep the accuracy gate but make AUC, precision, and recall the **blocking** gates. Also require that the new model doesn't regress more than 0.01 AUC against the currently approved model. | M8 |
| G17 | Phases 2, 3 | Data Wrangler and Autopilot now run inside **SageMaker Canvas**. Experiments may show up as **managed MLflow**, depending on the Studio domain. | Data Wrangler is optional for Part 2: the Processing job is the system of record. Autopilot stays optional. Choose the tracking backend in M0 (decision OD-2). | M0 |

---

## 4. Target Architecture

```text
 Source systems (CRM, Billing, Network, Support, Analytics)
        │  daily/monthly CSV drops + _MANIFEST.json
        ▼
 ┌──────────────────────────── Amazon S3 data lake (SSE-KMS, versioned) ───────────────────────────┐
 │ raw-data/ → processed-data/ → training/ → models/ → predictions/ → monitoring/ → artifacts/      │
 └──────────────────────────────────────────────────────────────────────────────────────────────────┘
        │ S3 → EventBridge (manifest object created)      EventBridge schedule (1st Sunday 02:00)
        └──────────────────────────┬──────────────────────────────────┘
                                   ▼
 ┌──────────────────────── SageMaker Pipeline: CustomerChurnPipeline ────────────────────────┐
 │ Preprocess (Processing) → Feature Engineering → Feature Store ingest (offline + online)    │
 │ → Train/Tune (XGBoost HPO; Debugger rules) → Evaluate (PropertyFile) → Clarify (SHAP+bias) │
 │ → Condition: KPI gates + no-regression → Register (PendingManualApproval) │ else Fail      │
 └────────────────────────────────────────────────────────────────────────────────────────────┘
        │ Model Registry "Customer-Churn-Models"  ── human approval ──┐
        ▼                                                             ▼
 EventBridge: Model Package State Change (Approved) → Step Functions deploy state machine
        │   deploy staging → smoke + latency test → prod blue/green canary → SNS notify
        ▼
 ┌───────────── Real-time path ─────────────┐        ┌──────────── Batch path ────────────┐
 │ Client → API Gateway (REST, auth,        │        │ Feature Store offline snapshot     │
 │ throttling) → Lambda (validate, Feature  │        │ (Athena) → 5M scoring file shards  │
 │ Store GetRecord) → SageMaker endpoint    │        │ → Batch Transform (PipelineModel)  │
 │ [PipelineModel: preprocessor → XGBoost]  │        │ → predictions/ in S3 → marketing   │
 │ ≥2 instances, auto scaling, data capture │        └────────────────────────────────────┘
 └──────────────────────────────────────────┘
        │ data capture → monitoring/data-capture/
        ▼
 Model Monitor (data quality daily; model quality monthly w/ ground truth)
 + CloudWatch dashboard/alarms → SNS (ML Eng, Platform, Ops) → optional drift-triggered retrain
```

### 4.1 Key design decisions

| ADR | Decision | Rationale | Alternative rejected |
|---|---|---|---|
| ADR-1 | **Production model: XGBoost** (pending the M3–M4 comparison) | It's the strongest on tabular data, built in, supports Debugger rules, and is cheap to serve. | LightGBM (BYOC adds operational burden); Linear Learner (baseline) |
| ADR-2 | **Serve a PipelineModel** (sklearn preprocessor → XGBoost) for both real-time and batch | One transform path prevents training–serving skew, and data capture records the raw feature payload that Model Monitor baselines against. | Preprocessing inside Lambda, which duplicates logic and drifts |
| ADR-3 | **Feature computation goes in the Feature Store; model-specific encoding goes in the model** | Features can be reused across models, and Lambda can fetch them in milliseconds from the online store. | Clients sending every feature (Phase 8 example) |
| ADR-4 | **Threshold is a model artifact** | The precision/recall trade-off is a business decision. The threshold is stored in the registry metadata and applied in Lambda and in post-processing of batch output. | A hard-coded 0.5 |
| ADR-5 | **Retraining is triggered by a manifest file**, not each object | Five source files would otherwise start five executions. A `_MANIFEST.json` written last starts exactly one. | One trigger per CSV |
| ADR-6 | **Step Functions orchestrates deployment** | It uses infrastructure already provided, has visible state and retries, and calls SNS natively. | Deploying from GitHub Actions with long-lived credentials |
| ADR-7 | **Blue/green canary with auto rollback** for production | Zero downtime, with rollback driven by CloudWatch alarms (Phase 10, Task 10). | In-place endpoint update |
| ADR-8 | **EKS hosts the prediction API** (`churn-api`), reached through API Gateway → VPC Link → internal NLB. This replaces Lambda on the real-time path. | Decided at implementation: no cold starts, pooled connections, HPA, and zone-spread pods. | API Gateway → Lambda |
| ADR-9 | **Terraform** for all infrastructure (resolves OD-1) | Decided at implementation. The deploy state machine owns endpoints, and Helm owns the app release. | AWS CDK |
| ADR-10 | **LocalStack (Community) in Docker** for local tests. A local model server, DynamoDB and SQS stand in for SageMaker, Feature Store and the Pipeline. | Decided at implementation. The same Terraform modules run against LocalStack. | LocalStack Pro |

The implementation lives in [`customer-churn-mlops/`](customer-churn-mlops/). Its [`docs/architecture.md`](customer-churn-mlops/docs/architecture.md) records the remaining build-time decisions.

---

## 5. Conventions

### 5.1 Repository layout (extends Phase 10)

```text
customer-churn-mlops/
├── .github/workflows/
│   ├── ci.yml                    # lint, unit tests, pipeline-definition validation (PRs)
│   └── train.yml                 # on main: upsert pipeline + start execution
├── config/
│   ├── project.yaml              # bucket, region, prefixes, role ARNs, instance types
│   ├── features.yaml             # feature list, dtypes, categorical/numeric, Feature Group schema
│   └── quality_gates.yaml        # AUC/precision/recall/accuracy thresholds, regression tolerance
├── containers/lightgbm/          # Dockerfile, train, serve (BYOC)
├── src/
│   ├── data/generate_synthetic.py
│   ├── preprocessing.py          # clean, dedupe, impute, cap outliers
│   ├── feature_engineering.py    # 9 engineered features (pure functions)
│   ├── feature_store.py          # Feature Group create/ingest/snapshot
│   ├── train_rf.py               # sklearn RandomForest entry point
│   ├── preprocessor_serve.py     # ColumnTransformer model_fn/input_fn/output_fn
│   ├── evaluate.py               # metrics, threshold selection, evaluation.json, plots
│   └── utils.py
├── pipelines/pipeline.py         # SageMaker Pipeline definition
├── deployment/
│   ├── endpoint.py               # create/update endpoint, DeploymentConfig (blue/green)
│   ├── autoscaling.py
│   ├── monitoring.py             # data capture, baselines, schedules, alarms, dashboard
│   ├── batch_transform.py
│   ├── lambda/predict/handler.py
│   └── stepfunctions/deploy.asl.json
├── infra/                        # IaC for API GW, Lambda, EventBridge, SNS, Step Functions, alarms
├── notebooks/                    # 01_eda, 02_features, 03_training, 04_tuning, 05_eval_clarify
├── tests/{unit,integration,load}/
├── docs/                         # architecture, runbooks, ADRs, evaluation and explainability reports
├── requirements.txt
└── README.md
```

### 5.2 S3 data lake layout

The bucket is `teleconnect-churn-<name>-lab`, with Block Public Access, versioning, SSE-KMS, and a lifecycle rule that moves `monitoring/` and `logs/` to Infrequent Access after 30 days.

```text
raw-data/<source>/ingest_date=YYYY-MM-DD/<source>.csv     # immutable; source ∈ customers|billing|usage|support|churn
raw-data/ingest_date=YYYY-MM-DD/_MANIFEST.json            # written last → retrain trigger
processed-data/<dataset_version>/customer_churn_clean.parquet
feature-store/                                            # Feature Store offline store (Glue/Athena table)
training/<dataset_version>/{train,validation}/            # headerless, label-first CSV
training/<dataset_version>/test/                          # with header, for evaluation
models/<pipeline_execution_id>/                           # model.tar.gz, preprocessor
predictions/input/<run_date>/part-*.csv                   # 5M-row scoring snapshot, sharded
predictions/output/<run_date>/                            # customer_id, churn_probability, churn_flag
monitoring/{data-capture,baselines,reports,ground-truth}/
artifacts/<pipeline_execution_id>/{evaluation.json,clarify/,debugger/,plots/}
pipelines/                                                # pipeline definition JSON snapshots
logs/
```

### 5.3 Naming and tagging

| Resource | Name |
|---|---|
| Feature Group | `teleconnect-customer-features` (record id `customer_id`, event time `event_time`) |
| Experiment | `customer-churn-experiments` |
| Pipeline | `CustomerChurnPipeline` |
| Model Package Group | `Customer-Churn-Models` |
| Endpoints | `customer-churn-staging`, `customer-churn-prod` |
| API | `POST /v1/predict` |
| SNS topic | `customer-churn-alerts` |

Every resource is tagged with `project=teleconnect-churn`, `env=<lab|staging|prod>`, `owner=<team>`, and `cost-center=<cc>`.

---

## 6. Component Specifications

### 6.1 Feature set (`config/features.yaml`)

| Feature | Formula | Lab requirement |
|---|---|---|
| `average_monthly_spend` | `total_charges / (tenure_months + 1)` | Average Monthly Spend |
| `customer_lifetime_value` | `monthly_charges * tenure_months` | Customer Lifetime Value |
| `support_frequency` | `support_calls / (tenure_months + 1)` | Support Frequency |
| `usage_growth_rate` | `(data_usage_gb - data_usage_gb_prev_3m) / (data_usage_gb_prev_3m + 1)` | Usage Growth Rate (D2) |
| `complaint_ratio` | `complaint_count / (tickets + 1)` | Complaint Ratio |
| `payment_delay_score` | `avg_days_past_due / 30 + outstanding_balance / (monthly_charges + 1)` | Payment Delay Score (D2) |
| `customer_risk_score` | `2*complaint_count + support_calls + (10 - satisfaction_score)` | Customer Risk Score |
| `engagement_score` | Phase 3 formula, with inputs min-max normalised first | Phase 11 |
| `age_band` | `<25, 25–34, 35–49, 50–64, 65+` | Clarify bias facet |

Preprocessing rules:

* numeric nulls → median, with an added `<col>_was_missing` flag for columns that have more than 1% nulls
* categorical nulls → `"Unknown"` (not the mode), so missingness stays visible as signal
* outliers capped at the IQR fences, with the fences fitted on train
* duplicates removed on `customer_id` (latest `event_time` wins)
* split 70/15/15, stratified, `random_state=42`

### 6.2 Models and tuning

| Model | Implementation | Key settings | Role |
|---|---|---|---|
| XGBoost 1.7-1 | Built-in | `binary:logistic`, `eval_metric=auc`, `scale_pos_weight≈4.5`, Debugger rules | Primary candidate |
| LightGBM | BYOC image in ECR | `is_unbalance=true`, early stopping on validation AUC | Challenger |
| Random Forest | SKLearn 1.2-1 script mode | `class_weight="balanced"`, `n_estimators=300` | Challenger |
| Linear Learner | Built-in | Settings from G5 | Baseline |
| Autopilot | Canvas / AutoML v2 (optional) | 1-hour budget | Reference |

HPO configuration:

* **Ranges:** `eta` 0.01–0.3 (log), `max_depth` 3–10, `num_round` 100–500, `min_child_weight` 1–10, `gamma` 0–10, `subsample` 0.5–1.0, `alpha` 0–10, `lambda` 0–10
* **Objective:** `validation:auc` (maximise)
* **Search:** Bayesian, `max_jobs=30`, `max_parallel_jobs=5`, early stopping set to Auto
* **Training instances:** `ml.m5.2xlarge` for the full 1.75M-row training set

### 6.3 Real-time latency budget

| Hop | Budget (p99) |
|---|---|
| API Gateway overhead | 15 ms |
| Lambda (warm, provisioned concurrency) incl. validation | 10 ms |
| Feature Store online `GetRecord` | 15 ms |
| `InvokeEndpoint` network + PipelineModel (2 containers) | 50 ms |
| Response mapping and headroom | 60 ms |
| **Total** | **< 150 ms** |

The endpoint runs on `ml.c5.large` or `ml.m5.large` (picked by load test), with at least 2 and at most 6 instances. Data capture is set to 100% in the lab and 20% in production.

**API contract.** Request: `{"customer_id": "100042", "overrides": {...optional}}`. Response: `{"customer_id", "churn_probability", "churn_flag", "threshold", "model_version", "top_factors"?}`. Errors return 400 (validation), 404 (unknown customer), and 503 (endpoint unavailable). Auth uses an API key and usage plan in the lab, and IAM or a Cognito authorizer in production.

### 6.4 Batch scoring

1. Athena runs a point-in-time query on the Feature Store offline store, producing 5M rows that are written as about 50 CSV shards under `predictions/input/<run_date>/`.
2. The Batch Transform job uses the PipelineModel with `instance_count=4` and `ml.m5.xlarge` to start, plus `split_type="Line"`, `strategy="MultiRecord"`, `max_payload=6`, `max_concurrent_transforms=4`, `assemble_with="Line"`, `input_filter="$[1:]"`, `join_source="Input"`, and `output_filter="$[0,-1]"`.
3. Post-processing applies the registered threshold and writes Parquet to `predictions/output/<run_date>/`.
4. Sizing: measure throughput on 500k rows, then set `instance_count = ceil(5M / (throughput_per_instance × 25 min))`. Batch Transform hands out whole S3 objects, so the number of shards must be at least 4× the instance count.

### 6.5 SageMaker Pipeline

The pipeline parameters are `InputDataUri`, `DatasetVersion`, `ProcessingInstanceType`, `TrainingInstanceType`, `ModelApprovalStatus=PendingManualApproval`, `AucThreshold=0.90`, `PrecisionThreshold=0.85`, `RecallThreshold=0.80`, and `GitSha`.

| Step | Type | Output |
|---|---|---|
| `Preprocess` | ProcessingStep (SKLearnProcessor) | clean data, splits, `preprocessor.joblib`, baseline dataset |
| `IngestFeatures` | ProcessingStep | Feature Group records (offline + online) |
| `DataQualityCheck` | QualityCheckStep | data-quality baseline (`statistics.json`, `constraints.json`) for Model Monitor |
| `TuneXGBoost` | TuningStep (or TrainingStep using the last best hyperparameters, set by a parameter) | best model artifact |
| `Evaluate` | ProcessingStep + PropertyFile | `evaluation.json` (metrics, chosen threshold, plots) |
| `ClarifyExplainBias` | ClarifyCheckStep | SHAP and bias reports, explainability baseline |
| `GateKPIs` | ConditionStep | AUC, precision, recall ≥ thresholds and AUC ≥ approved AUC − 0.01 |
| `RegisterModel` | ModelStep (PipelineModel) | new version with `ModelMetrics`, `customer_metadata_properties` (dataset version, Git SHA, threshold, training date) |
| `FailOnGate` | FailStep | execution fails with the metric values in the message |

### 6.6 Monitoring and alarms

| Signal | Mechanism | Alarm | Action |
|---|---|---|---|
| End-to-end latency | API Gateway `Latency` p99 | > 150 ms for 3 of 5 minutes | SNS |
| Model latency | `ModelLatency` p99 (µs) | > 50,000 µs | SNS |
| Errors | `Invocation5XXErrors` / `Invocations` | > 2% (rollback alarm at > 5%) | SNS, plus rollback during deployment |
| Lambda errors and throttles | Lambda metrics | > 1% | SNS |
| CPU and memory | Endpoint instance metrics | CPU > 80% for 15 minutes | Scaling check |
| Feature drift | Model Monitor data quality, daily; `feature_baseline_drift_*` metrics | Drift distance > 0.2 on any top-10 SHAP feature | SNS, optional retraining |
| Missing features | Model Monitor completeness constraints | Any violation | SNS |
| Prediction distribution | Custom metric `MeanPredictedChurnRate` (hourly, from captured data) | Outside the training rate ± 5 percentage points | SNS |
| Model quality | ModelQualityMonitor, monthly, with ground truth from the 90-day lag | AUC < 0.88 or recall < 0.78 | SNS, retraining |
| Pipeline failures | EventBridge on pipeline execution status | Status `Failed` | SNS |

The dashboard `TeleConnect-Churn-Ops` has these widgets: invocations, p50/p99 latency (API and model), error rate, CPU and memory, instance count, drift metrics, prediction distribution, last pipeline status, and batch job duration.

### 6.7 CI/CD and promotion

* **`ci.yml`** runs on PRs:
  * `flake8`, `pytest tests/unit`
  * `python pipelines/pipeline.py --validate`, which builds `pipeline.definition()` without starting it
  * Dockerfile build for LightGBM
  * IaC validation
* **`train.yml`** runs on merge to `main`: it assumes a role through GitHub OIDC, upserts the pipeline, and calls `start_pipeline_execution(GitSha=$GITHUB_SHA)`.
* **Approval:** a reviewer checks the evaluation, Clarify, and bias reports in Studio, then sets the version to `Approved`.
* **Deploy state machine** (Step Functions, started by EventBridge `SageMaker Model Package State Change` with `Approved`):
  1. Create the model and endpoint config.
  2. Deploy or update `customer-churn-staging`.
  3. Run smoke tests through a Lambda (`/ping`, 20 golden records with expected probability ±0.02, p99 latency < 150 ms).
  4. Update `customer-churn-prod` with `DeploymentConfig.BlueGreenUpdatePolicy`: canary at 10% for 10 minutes, then the rest; `AutoRollbackConfiguration` is wired to the 5XX and latency rollback alarms.
  5. Publish the result to SNS.
* **Rollback paths:**
  * automatic, through the deployment guardrails while traffic is shifting
  * manual, through a runbook that sets the previous version to `Approved` and re-runs the state machine

---

## 7. Milestone Plan

Roles follow Phase 11: **SA** is the Solution Architect, **MLE** the ML Engineer, and **MLOps** the MLOps Engineer. Estimates are in engineer-days for a production-quality build. The lab timings from the guides are shown for reference.

| Milestone | Phases / Lab Parts | Owner | Estimate | Lab time | Depends on |
|---|---|---|---|---|---|
| M0 Foundations | Phase 1 | MLOps + SA | 1.5 d | 45–60 min | — |
| M1 Ingestion & EDA | Phase 2 / Part 1 | MLE | 1 d | 90–120 min | M0 |
| M2 Data prep, features, Feature Store | Phase 3 / Parts 2–3 | MLE | 2 d | 2–2.5 h | M1 |
| M3 Multi-model training & tracking | Phase 4 / Part 4 | MLE | 2 d | 2.5–3 h | M2 |
| M4 Hyperparameter tuning | Phase 5 / Part 5 | MLE | 1 d | 2–2.5 h | M3 |
| M5 Evaluation, Clarify, Debugger, Registry | Phases 6–7 / Parts 6–8 | MLE + SA | 2 d | 4.5–5.5 h | M4 |
| M6 Serving: endpoint, API, batch | Phase 8 / Parts 9–11 | MLOps | 2.5 d | 3–3.5 h | M5 |
| M7 Monitoring | Phase 9 (Tasks 1–10) / Part 12 | MLOps | 1.5 d | ~2 h | M6 |
| M8 Pipeline & retraining triggers | Phase 9 (Tasks 11–18) / Part 13 | MLOps + MLE | 2 d | ~2 h | M5 (M6 for deploy) |
| M9 CI/CD, blue/green, rollback | Phase 10 | MLOps | 2 d | 3–4 h | M6, M8 |
| M10 Capstone hardening & acceptance | Phase 11 | All | 1.5 d | 6–8 h | M0–M9 |
| **Total** | | | **~19 engineer-days** (about 2 weeks for a team of 3) | **~32 h** | |

**Critical path:** M0 → M1 → M2 → M3 → M4 → M5 → M6 → M9 → M10. M7 and M8 can run in parallel once M5 and M6 are done.

```text
Week 1:  M0 ▸ M1 ▸ M2 ▸ M3 ▸ M4
Week 2:  M5 ▸ M6 ▸ ┬ M7 ┬ ▸ M9 ▸ M10
                   └ M8 ┘
```

### M0: Foundations (Phase 1)

**Tasks**

1. Pick one region and create the bucket and layout from [§5.2](#52-s3-data-lake-layout), with a KMS key and lifecycle rules.
2. Create the IAM roles:
   * `SageMakerExecutionRole`, used by Studio, Processing, Training, and the Pipeline. Start from the guide's managed policies for the lab, then scope S3 to the project bucket.
   * `ChurnLambdaRole`, with `sagemaker:InvokeEndpoint` on the prod endpoint and `sagemaker:GetRecord` on the Feature Group.
   * `ChurnDeployRole`, used by Step Functions.
   * a GitHub OIDC role.
3. Set up the SageMaker Studio domain and user profile, a kernel with `sagemaker`, `boto3`, `pandas`, `scikit-learn`, `xgboost`, `shap`, and `pyarrow`, and an ECR repo named `churn-lightgbm`.
4. Scaffold the repository ([§5.1](#51-repository-layout-extends-phase-10)) and `config/project.yaml`. Resolve OD-1 to OD-4.
5. Build `generate_synthetic.py` (D1, D2) and generate 2.5M training rows plus 5M scoring rows. Check that churn is 18% ± 0.5%, nulls are in the 3–5% range, and duplicates are about 0.5%.

**Exit criteria:** every Phase 1 Task 15 check passes; synthetic data is in `raw-data/ingest_date=…/`; CI runs on an empty test suite.

### M1: Ingestion and EDA (Phase 2, Lab Part 1)

**Tasks**

1. Load the five sources from S3. Check that `customer_id` is unique per source and that the referential integrity between sources holds.
2. Left-join the sources on `customer_id`, using `churn` as the driving table.
3. Profile the data: missing values per column, skew (|skew| > 1 flagged for a log transform or capping), IQR outliers, churn distribution, churn by contract, region, and satisfaction, and correlations.
4. Optionally create a Data Wrangler flow in Canvas that exports a Data Quality and Insights report. The notebook is the deliverable of record.

**Outputs:** `notebooks/01_eda.ipynb`, `docs/data-exploration-report.md` (**Deliverable 1**), and `processed-data/<v>/integrated.parquet`.

**Exit criteria:** the report covers every Part 1 bullet, and the data-quality findings are fed into the preprocessing rules ([§6.1](#61-feature-set-configfeaturesyaml)).

### M2: Data preparation, features, Feature Store (Phase 3, Lab Parts 2–3)

**Tasks**

1. Write `preprocessing.py` and `feature_engineering.py` as pure, unit-tested functions, ordered as in G1.
2. Run them as a **SageMaker Processing job** (`SKLearnProcessor`, `ml.m5.2xlarge`) that writes the splits in the G4 format, `preprocessor.joblib`, and the Model Monitor baseline input.
3. Create the Feature Group `teleconnect-customer-features` (offline + online, `customer_id` as record id, `event_time` as event time) and ingest with `FeatureGroup.ingest(max_workers=…)` from the Processing job.
4. Show feature reuse: build the training set with an Athena point-in-time query against the offline store, and run `GetRecord` against the online store.

**Outputs:** `notebooks/02_features.ipynb` (**Deliverable 2**), `docs/feature-catalog.md` (business rationale for each feature), and the populated Feature Group.

**Exit criteria:**
* No nulls after preprocessing.
* Split churn rates are within ±0.5 percentage points of each other.
* All 9 engineered features are present.
* An Athena query returns 2.5M rows.
* Online `GetRecord` p99 is under 20 ms.

### M3: Multi-model training and experiment tracking (Phase 4, Lab Part 4)

**Tasks**

1. Train XGBoost, Linear Learner (with the G5 settings), and Random Forest (`train_rf.py`).
2. Build, push, and train the LightGBM BYOC container (`containers/lightgbm/`, following the SageMaker training toolkit conventions).
3. Optionally run an Autopilot job as a reference.
4. Log every job as an Experiments run, with parameters, validation AUC, precision, recall, and the artifact URI.
5. Set `use_spot_instances=True` with checkpointing on the tree models to reduce cost.

**Outputs:** 4 or 5 model artifacts under `models/` (**Deliverable 3**) and an experiment comparison view or chart (**Deliverable 5**).

**Exit criteria:** all four required algorithms finish successfully and appear in one experiment, and the champion is chosen by validation AUC.

### M4: Hyperparameter tuning (Phase 5, Lab Part 5)

**Tasks**

1. Run the tuning job from [§6.2](#62-models-and-tuning), with trial jobs linked to the experiment.
2. Compare the baseline against the best trial, and the champion against the challengers.
3. Save the best hyperparameters to `config/best_hparams.json`. The pipeline uses them when `TuneXGBoost` is skipped.

**Outputs:** `docs/hpo-results.md` with the tuning job table, the parameter-importance view, and the baseline-to-tuned delta (**Deliverable 4**).

**Exit criteria:** validation AUC is above 0.90.

### M5: Evaluation, explainability, debugging, registry (Phases 6–7, Lab Parts 6–8)

**Tasks**

1. Write `evaluate.py`:
   * Compute accuracy, precision, recall, F1, ROC AUC, PR AUC, the confusion matrix, and ROC and PR curves on the **test** set.
   * Select the threshold on the **validation** set: the highest precision subject to recall ≥ 0.80.
2. Run Clarify:
   * SHAP with a baseline from the k-means centroids of train, over a 5,000-row sample for global and local explanations.
   * Pre-training bias (CI, DPL) and post-training bias (DPPL, DI, recall difference) on gender, age band, and region.
3. Re-train the champion with Debugger rules (G8) and document the findings: overfitting, convergence, dead features. Use `tree_depth` and gain importance where they apply.
4. Create the Model Package Group and register the PipelineModel with `ModelMetrics` (evaluation, Clarify, data-quality baselines), the metadata from Phase 7 Task 9, and the Git SHA. Show approval and rejection, version comparison, and lineage (`LineageQueryRequest`).

**Outputs:** `docs/evaluation-report.md` and `docs/explainability-bias-report.md` (**Deliverable 6**), the registered version (**Deliverable 7**), and the Debugger report in `artifacts/`.

**Exit criteria:**
* Test-set AUC, precision, and recall meet R1–R3.
* There's no bias metric with |DPPL| > 0.1 that hasn't been explained.
* The version is `PendingManualApproval` and then `Approved`, with full metadata.

### M6: Serving: endpoint, API, batch (Phase 8, Lab Parts 9–11)

**Tasks**

1. Deploy the approved PipelineModel to `customer-churn-staging`, then to `customer-churn-prod` with ≥ 2 instances and data capture enabled.
2. Health checks: the container's `/ping` is covered by the SageMaker health check; add a synthetic canary (CloudWatch Synthetics or a scheduled Lambda) that calls `/v1/predict` every minute.
3. Set up auto scaling (G11) with scale-in and scale-out cooldowns of 300 and 60 seconds.
4. Show a **rolling update** on staging (`RollingUpdatePolicy`, batch size of 1 instance) to cover Part 9.
5. Build the Lambda `predict` handler (validation, `GetRecord`, `InvokeEndpoint`, applying the threshold, structured JSON logs, provisioned concurrency of 2).
6. Build API Gateway with a REST `POST /v1/predict`, an API key and usage plan, throttling, and request validation, all defined in IaC.
7. Run the 5M batch scoring job from [§6.4](#64-batch-scoring) and record its duration.
8. Load test with Locust or `hey` at the expected peak RPS (OD-3) × 2 for 15 minutes to set the auto-scaling target.

**Outputs:** the endpoint (**Deliverable 8**), predictions in `predictions/output/` (**Deliverable 9**), and the API URL and Postman collection (**Deliverable 10**).

**Exit criteria:**
* The API returns a valid response, with p99 under 150 ms at peak.
* Auto scaling adds instances under load.
* The batch job finishes in under 30 minutes for 5M rows, and every input `customer_id` appears in the output.

### M7: Monitoring (Phase 9 Tasks 1–10, Lab Part 12)

**Tasks**

1. Confirm data capture is working and inspect the captured JSONL.
2. Create the data-quality baseline (pipeline output) and a daily `DefaultModelMonitor` schedule with `enable_cloudwatch_metrics=True`.
3. Create the ground-truth merge job and a monthly `ModelQualityMonitor` schedule (G12).
4. Add the custom metric `MeanPredictedChurnRate` (a scheduled Lambda over the captured data).
5. Build the dashboard and alarms from [§6.6](#66-monitoring-and-alarms), with the SNS topic and email subscriptions.
6. **Drift simulation:** send traffic with shifted `monthly_charges` (+40%) and `satisfaction_score` (−2), run the monitor on demand, and confirm the violation and the alarm.

**Outputs:** the CloudWatch dashboard (**Deliverable 11**) and a monitoring runbook in `docs/runbooks/monitoring.md`.

**Exit criteria:** the drift simulation produces a violation report and an SNS email, and every alarm has been triggered at least once in testing.

### M8: Automated retraining pipeline (Phase 9 Tasks 11–18, Lab Part 13)

**Tasks**

1. Implement `pipelines/pipeline.py` as described in [§6.5](#65-sagemaker-pipeline) and upsert it.
2. Create the EventBridge schedule `cron(0 2 ? * SUN#1 *)` → `CustomerChurnPipeline`, passing the latest `ingest_date` as a parameter.
3. Enable S3 → EventBridge notifications. Add a rule on `Object Created` with key suffix `_MANIFEST.json` under `raw-data/` that targets the pipeline (ADR-5).
4. Optional: a drift alarm triggers the pipeline through EventBridge, rate-limited to once per 7 days.
5. Connect approval to deployment through the EventBridge rule → Step Functions (completed in M9).

**Outputs:** the pipeline definition and execution history (**Deliverable 12**).

**Exit criteria:**
* Uploading a manifest starts exactly one execution.
* A failing gate (for example, with `AucThreshold=0.99`) ends in `FailOnGate`.
* A passing run registers a new version as `PendingManualApproval`.

### M9: CI/CD, blue/green, rollback (Phase 10)

**Tasks**

1. Write `ci.yml` and `train.yml` ([§6.7](#67-cicd-and-promotion)) and protect `main` with required checks.
2. Build the deploy state machine: staging, smoke tests, blue/green canary in production with auto rollback, SNS.
3. **Rollback test:** deploy a deliberately broken model version (for example, an inference script that returns 500 on 10% of requests) and check that the guardrails roll back to the previous version within the bake window.
4. Write the runbook for manual rollback by re-approving the previous version.

**Outputs:** the GitHub workflows, the state machine, `docs/cicd.md`, and evidence of the rollback test.

**Exit criteria:** every Phase 10 Task 11 step runs end to end from a single commit.

### M10: Capstone hardening and acceptance (Phase 11)

**Tasks**

1. Run the acceptance suite in [§9](#9-acceptance-test-plan).
2. Do a security pass ([§10](#10-security-and-compliance)) and set up cost controls ([§11](#11-cost-management)).
3. Finish the architecture diagram and the presentation (the 10 topics in Phase 11).
4. Check against the rubric.

**Exit criteria:** all 10 acceptance tests pass, and the 12 deliverables are linked from the README.

---

## 8. Test Strategy

| Level | Scope | Tooling | Gate |
|---|---|---|---|
| Unit | Preprocessing, feature formulas (divide-by-zero, nulls, negatives), threshold selection, Lambda handler validation | pytest | CI on every PR |
| Data contract | Schema, dtypes, null rates, allowed categories, churn label ∈ {0,1} | pytest + `features.yaml`, Model Monitor constraints | Pipeline `DataQualityCheck` |
| Pipeline | `pipeline.definition()` builds; parameters resolve | pytest | CI |
| Model quality | KPI gates and no-regression check | `evaluate.py` + ConditionStep | Pipeline |
| Inference contract | 20 golden records produce the expected probability ±0.02 on staging; error codes 400, 404, 503 | pytest integration | Deploy state machine |
| Performance | p99 < 150 ms at 2× peak; 5M batch < 30 min | Locust or `hey`; timed Batch Transform | M6 exit, before each production release |
| Resilience | Kill one endpoint instance or force 5XX; rollback | Manual game day | M9 exit |

---

## 9. Acceptance Test Plan

This is the Phase 11 suite, with the deliverable each test provides evidence for.

| # | Test | Expected result | Evidence | Milestone |
|---|---|---|---|---|
| AT-1 | Upload new training data and manifest | Pipeline starts automatically (once) | EventBridge rule metrics, execution ID | M8 |
| AT-2 | Train new model | Training and tuning complete | Pipeline step status | M8 |
| AT-3 | Evaluate model | AUC > 0.90, precision > 85%, recall > 80% | `evaluation.json` | M5, M8 |
| AT-4 | Register model | New version, `PendingManualApproval` | Model Registry | M8 |
| AT-5 | Approve model | Staging → production deployment runs | Step Functions execution | M9 |
| AT-6 | Invoke REST API | Prediction returned, p99 < 150 ms | curl output, load-test report | M6 |
| AT-7 | Run Batch Transform | 5M predictions in S3 in < 30 min | Job duration, row count | M6 |
| AT-8 | Simulate feature drift | Violation and SNS alert | Monitor report, email | M7 |
| AT-9 | Trigger retraining | Scheduled and manual executions succeed | Execution history | M8 |
| AT-10 | Validate rollback | Previous model restored automatically | Endpoint config history, alarm timeline | M9 |

Each of the 12 problem-statement deliverables maps to a milestone:

| Deliverable | Milestone |
|---|---|
| 1. Data exploration report | M1 |
| 2. Feature engineering notebook | M2 |
| 3. Trained ML models | M3 |
| 4. Hyperparameter tuning results | M4 |
| 5. Experiment tracking dashboard | M3 |
| 6. Model explainability report | M5 |
| 7. Registered model in Model Registry | M5 |
| 8. Real-time inference endpoint | M6 |
| 9. Batch prediction output | M6 |
| 10. API endpoint for online inference | M6 |
| 11. CloudWatch monitoring dashboard | M7 |
| 12. Automated SageMaker Pipeline for retraining | M8 |

---

## 10. Security and Compliance

* **Encryption:** SSE-KMS on the bucket, Feature Store (offline and online), data capture, and model artifacts; `enable_network_isolation` on training jobs; inter-container traffic encryption for distributed jobs.
* **Least privilege:** separate roles per component (M0). `AmazonS3FullAccess` is used in the lab only. Before M10, replace it with bucket-scoped policies.
* **Personal data:** age, gender, and region are personal attributes. They're used as Clarify facets. Decide whether `gender` stays in the model as a feature (OD-4). Mask `customer_id` in Lambda logs and don't log feature payloads.
* **API:** API key and usage plan (lab), IAM or Cognito (production), request validation, throttling. AWS WAF is optional.
* **Network (production):** VPC-only Studio, VPC endpoints for S3, SageMaker API and Runtime, and STS.
* **Audit:** CloudTrail for SageMaker API calls; Model Registry approval history is the governance record.

---

## 11. Cost Management

| Item | Control |
|---|---|
| Real-time endpoints | Delete staging after validation; consider Serverless Inference for staging; production minimum of 2 instances is required by the SLA |
| Training and tuning | Spot instances with checkpoints; `max_parallel_jobs=5`; warm pools only during HPO sessions |
| Clarify and Debugger | SHAP on a 5k sample; turn off Debugger profiling after M5 |
| Feature Store online store | Disable the online store or set a TTL in non-production if it isn't needed |
| Model Monitor | Daily schedule, not hourly; 20% capture sampling in production |
| Lab teardown | `scripts/teardown.py` deletes endpoints, monitoring schedules, the Feature Group online store, and Studio apps |

Set an AWS Budget alert on the `project=teleconnect-churn` tag.

---

## 12. Risks and Open Decisions

### 12.1 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| KPIs aren't met: precision > 85% and recall > 80% at once, with 18% prevalence, is a demanding target | Medium | High | Synthetic generator with a controlled signal (D1); threshold tuning (ADR-4); feature iteration in M2–M4; escalate the trade-off to the business with the PR curve |
| Batch job exceeds 30 minutes | Low | Medium | Shard input; scale instances using the measured throughput (§6.4) |
| Latency breached by Lambda cold starts or the Feature Store lookup | Medium | Medium | Provisioned concurrency; latency budget; p99 alarm |
| Training–serving skew | Medium | High | PipelineModel (ADR-2); golden-record contract test |
| The 90-day label lag hides model decay | High | Medium | Prediction-distribution and feature-drift early warnings (G12) |
| Feature names or availability in Studio differ (Data Wrangler or Experiments moved into Canvas or MLflow) | Medium | Low | Decide the tracking backend in M0 (OD-2) |
| Lab cost overrun from idle endpoints | High | Low | Teardown script; budgets |

### 12.2 Open decisions (resolve in M0)

| ID | Decision | Default if undecided |
|---|---|---|
| OD-1 | IaC tool for API Gateway, Lambda, EventBridge, Step Functions, and alarms: CDK, CloudFormation, or Terraform | **Resolved: Terraform** (ADR-9) |
| OD-2 | Experiment tracking backend: SageMaker Experiments or managed MLflow | Whichever the Studio domain shows; the SDK code is wrapped in `utils.track_run()` |
| OD-3 | Expected real-time peak RPS from support interactions | 50 RPS (needed for load testing and scaling targets) |
| OD-4 | Whether `gender` is used as a model feature, or only as a bias facet | Facet only |
| OD-5 | Production approvers: who approves model versions | ML lead and retention business owner |

---

## 13. Optional Extensions Backlog

From the Phase 11 advanced challenges, in priority order:

1. Shadow deployment of the challenger (LightGBM) using SageMaker shadow variants
2. A multi-account setup (dev, staging, prod) with cross-account Model Registry sharing
3. Serverless or asynchronous inference for the staging and low-traffic paths
4. QuickSight executive dashboard over `predictions/output/` (churn risk by segment, revenue at risk)
5. Kinesis-based near-real-time feature updates (for example, support-ticket events updating the online store)
