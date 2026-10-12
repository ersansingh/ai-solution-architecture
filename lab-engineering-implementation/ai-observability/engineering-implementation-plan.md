# Engineering Implementation Plan: Enterprise AI/ML Observability Platform (AWS Multi-Account, Hybrid Multi-Cloud)

> **Requirements spec:** [`observability-requirements-spec.md`](observability-requirements-spec.md)
> **Implementation guides:** [`implementation-guide/`](implementation-guide/) (Parts 1–6)
> **Plan date:** 2026-10-10

---

## 1. Purpose and Scope

This plan turns the observability requirements spec and the six implementation-guide parts into one engineering build plan. It defines:

* the target architecture and the decisions that the guides leave open or contradict
* a telemetry contract (names, attributes, cardinality rules) that every team emits against
* milestones, tasks, owners, estimates, and exit criteria
* the bugs and gaps in the guide code that have to be fixed before the targets are achievable
* the test, fault-injection, security, and cost controls for the platform itself

**In scope:**
* the five telemetry pillars from spec section 4 (infrastructure, data and features, model performance, GenAI/LLM, tracing and logging)
* compliance and security monitoring and the five closed-loop remediations from spec section 5
* hybrid ingestion from Azure, GCP, and on-premises GPU nodes
* the dashboards and alert matrix from Part 6

**Out of scope:**
* building the monitored workloads themselves: the fraud, churn, and credit-risk models, and the RAG assistant
* migrating existing tooling
* QuickSight executive reporting beyond the ROI datasets (backlog, [§14](#14-backlog))

---

## 2. Requirements and Design Response

| # | Requirement (spec) | Target | Design response |
|---|---|---|---|
| R1 | Platform availability | 99.99% | SLOs with multi-window, multi-burn-rate alerts ([§6.6](#66-slos-and-alerting)). The telemetry pipeline is multi-AZ with persistent queues, so losing observability never blocks a workload. |
| R2 | Time to first token (TTFT) | < 300 ms p95 | Streaming instrumentation (`ConverseStream`) measured at the first content chunk, not at full response (fixes G9) |
| R3 | Time per output token (TPOT) | < 30 ms | Inter-chunk histogram from the same streaming wrapper |
| R4 | RAG end-to-end latency | < 1.5 s p95 | Root span per RAG request with child spans for retrieve, rerank, generate, and guardrail. Alert on the root-span duration p95. |
| R5 | Real-time prediction latency | < 10 ms p99 at 500k QPS | Measured at the serving tier (Triton on EKS, OD-3). Predictions logged asynchronously to a stream instead of 100% synchronous data capture (G8). |
| R6 | Throughput | 500k events/s, 5k prompts/min, 2M tokens/min | Two-tier OpenTelemetry (OTel) gateways sized by load test. Persistent sending queues. Spans are converted to metrics *before* sampling. |
| R7 | Cost | ≤ $0.015 per RAG query; $500/day soft and $1,000/day hard per department | Bedrock application inference profiles tagged per department, plus live token cost metrics. The hard cap triggers cost routing (AppConfig flag). |
| R8 | Infrastructure metrics | GPU (DCGM), pods, nodes, Lambda | Agent tier: ADOT DaemonSet, DCGM exporter, kube-state-metrics, node exporter → Amazon Managed Service for Prometheus (AMP). Lambda through the ADOT layer and CloudWatch. |
| R9 | Data quality | Freshness < 30 min, volume ±20%, schema drift, PSI > 0.25, PII | Glue Data Quality (built on Deequ) rulesets, Glue Schema Registry with BACKWARD compatibility, a PSI job, and Macie discovery jobs |
| R10 | Model quality | Accuracy ≥ 92%, precision ≥ 88%, recall ≥ 85%, F1 ≥ 86%, AUC ≥ 0.90, ECE ≤ 0.05, SHAP rank shift ≤ 2 | Per-model SLO config, a ground-truth join on a stream, a scheduled evaluator with a corrected ECE, and a SHAP rank-shift job |
| R11 | RAG quality | Groundedness ≥ 0.85, context recall ≥ 0.80, context precision ≥ 0.82 | Sampled online LLM-judge scoring (groundedness, context precision) plus an offline golden set (context recall needs reference answers) |
| R12 | Safety | Prompt injection, toxicity, PII | Bedrock Guardrails with a `PROMPT_ATTACK` filter (missing in the guide), guardrail trace metrics, and a session denylist |
| R13 | Agents | Tool failure < 5%, loop iterations < 5 | LangGraph instrumentation: tool spans, iteration counter, failure ratio |
| R14 | Tracing | OTLP with required attributes; 100% errors and > 2.5 s, 5% otherwise | Trace-ID-aware load balancing → tail sampling. Required attributes are enforced in the telemetry contract ([§5](#5-telemetry-contract)). |
| R15 | PII scrubbing | SSN, credit card, API keys removed before export | Redaction runs at the agent tier (first pass) and the gateway tier (enforced), across spans, logs, and events. A canary test proves it. |
| R16 | Audit and security | CloudTrail, Config, Security Hub, GuardDuty | Organization trail and delegated administrators in a Security account, a Config aggregator, and Security Hub standards |
| R17 | Closed-loop remediation | Five automated responses | An event-driven remediation framework with idempotency, cooldowns, approval tiers, and an audit trail ([§6.7](#67-closed-loop-remediation)) |

---

## 3. Gaps and Corrections to the Inputs

Each finding is assigned to a milestone. Severity: **H** = output wrong or requirement unmet, **M** = works but fragile or costly, **L** = hygiene.

### 3.1 Architecture-level

| ID | Sev | Source | Finding | Resolution | Milestone |
|---|---|---|---|---|---|
| A1 | H | Part 6 §5 | `resourcedetection` with `[env, gcp, ecs, ec2, eks, azure]` runs in the **central** gateway, so it detects the gateway's own cloud. With `override: false`, every attribute the source didn't set is stamped with the gateway's AWS values, which corrupts `cloud.provider` and `cloud.region` for Azure and GCP telemetry. | Resource detection and `k8sattributes` run only at the **agent tier** in each environment. The gateway rejects or flags data missing `cloud.provider`. | M1 |
| A2 | H | Part 6 §5 | Tail sampling on a multi-replica gateway without trace-ID routing splits a trace's spans across replicas, so sampling decisions are wrong and traces arrive incomplete. | Two gateway tiers: tier 1 uses the `loadbalancing` exporter, routed by `traceID`; tier 2 runs `tail_sampling`. | M1 |
| A3 | H | Part 6 §5 | Sampling at 5% before generating latency and error metrics makes RED dashboards and SLOs wrong by 20×. | Run the `spanmetrics` connector on unsampled spans (tier 1) and export to AMP. Only traces are sampled. | M1 |
| A4 | H | Parts 2–5 vs Part 6 §7 | Parts 2–5 push quality metrics to **CloudWatch** (`put_metric_data`), but the Part 6 Prometheus rules alert on them as if they were in **AMP** (`Enterprise_ModelObservability_Recall`). Nothing moves them there. | Decide each signal's system of record ([§4.2](#42-key-design-decisions), ADR-3). Low-frequency ML, data, and RAG quality metrics live in CloudWatch, whose alarms drive EventBridge natively. High-volume runtime metrics live in AMP. Grafana reads both. | M0 |
| A5 | M | Part 1 vs Part 6 | Trace and log destinations conflict: Part 1 sends traces to X-Ray and logs to CloudWatch, Part 6 sends both to Observe, and the spec lists both. Dual-writing everything doubles cost. | One system of record per signal (ADR-3, OD-1). CloudWatch Logs keeps only the AWS-native, audit, and retention-mandated streams. | M0 |
| A6 | M | Spec §2 vs Part 6 §8 | The spec says Amazon Managed Grafana (AMG); Part 6 says Grafana Enterprise. | Default AMG with data sources for AMP, CloudWatch, X-Ray, Observe, and Athena. Grafana Enterprise only if on-premises users need it (OD-2). | M0 |
| A7 | H | Spec §3 / Part 3 | A 10 ms p99 at 500k QPS is unrealistic on SageMaker real-time endpoints with **100%** data capture: capture adds request overhead and writes about 1.3 trillion records a month to S3. | Fraud serving on Triton on EKS (spec §2 already lists it), or SageMaker with sampled capture (OD-3, OD-4). Prediction events go to Kinesis or MSK → Firehose → Parquet for the ground-truth join. | M4 |
| A8 | M | Spec §1 | The spec links point to non-existent paths (`lab6-observability-governance/...`), and Part 6 links to `file:///c:/Users/DELL/...`. | Fix the links to relative repository paths. | M0 |
| A9 | M | Part 6 §14 | The roadmap is five sequential two-week phases. It has no foundations phase (accounts, cross-account access, telemetry contract), no multi-cloud phase, and no remediation-framework phase. | Use the milestone plan in [§7](#7-milestone-plan). | — |

### 3.2 Code-level

| ID | Sev | Source | Finding | Resolution | Milestone |
|---|---|---|---|---|---|
| G1 | H | Part 1, Part 6 `transform` | Redaction only rewrites `attributes["payload"]` on **logs**. Span attributes, span events, log bodies, and metric labels aren't scrubbed. Credit cards and API keys aren't covered at all. | Add a `redaction` processor (blocked-value regexes for SSN, Luhn-validated PAN, AWS keys `AKIA[0-9A-Z]{16}`, `sk-…` secrets, JWTs) **and** `transform` `trace_statements` and `log_statements` on `body` and every attribute. Prove it with a PII canary test. | M1 |
| G2 | M | Part 1 | The DCGM exporter is scraped from the **gateway** by a static target every 5 s. That doesn't scale to many nodes and breaks off-cluster. | Scrape per node at the agent tier using Kubernetes service discovery, at 15 s. Use 5 s only for an opt-in debug job. | M2 |
| G3 | M | Part 2 | The PSI alarm notifies SNS, but the text says it "triggers retraining". Nothing connects them. PSI also only handles numeric features. | Alarm state change → EventBridge → data-remediation state machine. Add categorical PSI (per-category share) and minimum-sample guards. | M3, M7 |
| G4 | M | Part 2 | Freshness (< 30 min), volume (±20%), schema-registry checks, and Macie are required but not implemented. The Deequ example also hard-codes a date partition. | Glue Data Quality rulesets (`DataFreshness`, `RowCount` with anomaly detection, `ColumnValues`, `IsUnique`), Schema Registry compatibility checks for producers, and Macie scheduled discovery jobs. All runs are parameterised by partition. | M3 |
| G5 | H | Part 3 | The ground-truth "EventBridge" handler parses `event['Records'][i]['body']`, which is SQS's shape. Unmatched labels are logged and **dropped** ("writing to pending queue" never happens). It writes one S3 object per prediction (the small-files problem at 500k QPS). No component populates `PredictionLookup`. | Prediction events → Kinesis or MSK. Ground truth → SQS with a DLQ and a delayed-retry queue. The join is a Flink or Glue streaming job (or a Lambda for low-QPS models) writing to Firehose → partitioned Parquet. DynamoDB lookup with TTL only for low-QPS models. | M4 |
| G6 | H | Part 3 | The ECE function compares bin **accuracy of the 0.5 decision** with mean probability. For binary calibration it must compare the **observed positive rate** with mean predicted probability per bin, so the guide's code over- or under-reports ECE. | `ece = Σ_b (n_b/N) · |mean(y_true_b) − mean(p_b)|`, unit-tested against a known calibration curve | M4 |
| G7 | M | Part 3 | Rollback targets a hard-coded `TargetStableVersion: "2.0.0"`, and the state machine has no guard against repeated rollbacks or rolling back to an equally drifted model. | Resolve the previous **Approved** package from the Model Registry. Add a DynamoDB lock and cooldown (one auto-rollback per model per 24 h), then escalate. | M7 |
| G8 | M | Part 3 | 100% `data_capture_config` on the fraud endpoint (see A7). The Terraform also lacks `kms_key_id`. | Sampling percentage per model from config (100% for low QPS such as churn, 1–5% for fraud), plus KMS | M4 |
| G9 | H | Part 4 | The "TTFT" histogram records the **whole** non-streaming `invoke_model` latency. TPOT isn't measured. Attribute names (`genai.system`) don't follow the OTel GenAI semantic conventions (`gen_ai.*`), and the Part 6 alert queries a metric (`gen_ai_client_time_to_first_token_seconds_bucket`) that nothing emits. | Streaming wrapper over `ConverseStream`: TTFT at the first `contentBlockDelta`, TPOT between deltas, `gen_ai.*` attributes, metric names fixed in the contract ([§5](#5-telemetry-contract)). Alerts are generated from the same contract. | M5 |
| G10 | H | Part 4 | Raw prompts and completions are written to S3 **unredacted** and **synchronously** in the request path (`put_object` per call). | Async: span event → gateway redaction → Firehose → S3 (KMS, 30-day lifecycle). The payload store keeps only what passed redaction. | M5 |
| G11 | H | Part 4 | Judge evaluator bug: `json.loads(res['body'].read()['content'][0]['text'])` indexes bytes, so it raises `TypeError` on every call. Only groundedness exists; context recall and precision are missing. Scoring every query roughly doubles LLM cost against a $0.015 budget. | Fix the parsing and enforce structured JSON output with a schema-validated retry. Add context-precision scoring online and context recall offline on a golden set. Sample at 5–10% (OD-5), with stratified 100% sampling for flagged sessions. | M5 |
| G12 | H | Part 4 | The Guardrail Terraform has **no `PROMPT_ATTACK` filter**, so the spec's injection detection is unimplemented. It's also missing the required `blocked_input_messaging` and `blocked_outputs_messaging` and a published version. Contextual grounding at 0.85 as a **blocking** filter would block responses that the spec only wants alerted (the reroute is at < 0.70). | Add `PROMPT_ATTACK` (input HIGH), `MISCONDUCT`, and `INSULTS` filters, the messaging fields, and `aws_bedrock_guardrail_version`. Set blocking grounding to 0.70 and monitor at 0.85 from the judge metric. | M5 |
| G13 | M | Part 4 | The pricing table and model IDs are hard-coded and outdated (Claude 3.x). Cost is pushed with a synchronous `put_metric_data` per call. | Pricing in versioned config (S3/AppConfig) keyed by inference profile. Cost is computed from token metrics in the pipeline (OTel → AMP). Reconcile daily against the Cost and Usage Report (CUR). | M5, M6 |
| G14 | M | Part 4 | The fallback "switches to Claude Haiku" for low groundedness, but a smaller model isn't inherently more grounded. Routing is written by a Lambda nobody reads. | The routing mode is an **AWS AppConfig** flag the app polls. `STRICT_GROUNDING` switches the prompt template (cite-only, refuse when unsupported), enables guardrail grounding blocking, and sets temperature 0. Model choice comes from config. | M5, M7 |
| G15 | H | Part 4/5 | Agent metrics (tool latency, failure rate, loop iterations), OpenSearch retrieval tracing, and the prompt-injection "block session" action aren't implemented anywhere. | LangGraph and OpenSearch instrumentation, a session denylist in DynamoDB checked by the API, and a SOC page through PagerDuty | M5, M7 |
| G16 | M | Part 5 | The ROI code divides revenue by **token cost per transaction**, which ignores infrastructure cost and operational savings that the formula includes. | Compute ROI daily in Athena from CUR (infrastructure + tokens), the business-outcome table, and inference counts. Real-time panels show only cost per inference. | M6 |
| G17 | H | Part 5 | ITSM Lambda: a default PagerDuty key is hard-coded in code. There's no ServiceNow call, despite the title. There's no `dedup_key` and no resolve on `OK`, so incidents pile up. | Secrets in Secrets Manager. `dedup_key = alarm ARN`, with resolve on `OK`. ServiceNow Table API with correlation ID. Retries and a DLQ. | M6 |
| G18 | H | Part 5 | Governance state machine: `"BucketName": "$.detail.bucketName"` lacks the `.$` suffix, so it passes a **literal string**. Macie, GuardDuty, and Config findings aren't CloudWatch alarms, so `Choice` on `alarmName` never matches them. "Unauthorized-Model-Modification" has no detection source. Fully automated IAM revocation is high-risk. | Route findings by EventBridge `source` and `detail-type`. Detect model changes with a CloudTrail → EventBridge rule on `sagemaker:UpdateEndpoint`, `DeleteModelPackage`, and `UpdateModelPackage` by a principal outside the pipeline roles. Quarantine with a deny-tag and bucket policy. IAM revocation needs approval (OD-6). | M6, M7 |
| G19 | M | Spec §4E | `prediction_id` and `tenant_id` are required attributes. If they leak into **metric labels**, AMP cardinality explodes. | Contract rule: `prediction_id`, `session_id`, `user_id`, and `trace_id` are span and log attributes only, never metric labels. `tenant_id` and `department` are allowed as bounded labels. Gateway `attributes` processors drop the forbidden labels from metrics. | M1 |
| G20 | M | Spec §4E | "100% for http.status_code ≥ 500" uses `status_code: ERROR`, which only works if instrumentation sets span status on 5xx. | Add a `numeric_attribute` policy on `http.response.status_code` 500–599 alongside `status_code`. | M1 |
| G21 | M | Spec §4C | SHAP rank shift > 2 is required but not implemented. A single global threshold set (92% accuracy) doesn't fit fraud, churn, and credit risk alike. | A weekly SHAP rank-shift job compares the top-10 rank vectors with the baseline. Per-model SLO files override the defaults. | M4 |

---

## 4. Target Architecture

### 4.1 Topology

```text
 ┌─────────────── Workload accounts (AWS prod-ml, prod-genai) ───────────────┐   ┌── Azure / GCP / on-prem ──┐
 │ EKS / ECS / EC2 / Lambda / SageMaker / Bedrock / OpenSearch Serverless /  │   │ AKS / GKE / bare-metal    │
 │ MSK / Kinesis / S3 / Glue / Feature Store                                 │   │ GPU K8s (DCGM)            │
 │  App SDKs: OTel GenAI wrapper, LangGraph + OpenSearch instrumentation     │   │ OTel agent (DaemonSet)    │
 │  AGENT TIER: ADOT DaemonSet (resourcedetection, k8sattributes, DCGM/node/  │   │ resourcedetection,        │
 │  KSM scrape, first-pass redaction) · ADOT Lambda layer · ECS sidecar      │   │ first-pass redaction      │
 └──────────────┬────────────────────────────────────────────────────────────┘   └────────────┬──────────────┘
                │ OTLP/gRPC (PrivateLink)                     OTLP/gRPC mTLS (VPN / DX / Interconnect)
                ▼                                                                             ▼
 ┌──────────────────────────────── Observability account ─────────────────────────────────────────────┐
 │ NLB → GATEWAY TIER 1 (stateless, HPA): memory_limiter, contract validation, redaction (enforced),   │
 │        cardinality guard, spanmetrics connector → AMP, loadbalancing exporter (by traceID)         │
 │      → GATEWAY TIER 2 (StatefulSet): tail_sampling (errors, 5xx, >2.5 s, 5% probabilistic), batch  │
 │ Exports: metrics → AMP (remote write)   traces + logs → Observe (OTLP)   audit/AWS logs → CW Logs  │
 │ AMG (AMP, CloudWatch via OAM, X-Ray, Observe, Athena)   AMP Alertmanager → SNS                     │
 │ CloudWatch cross-account observability (OAM sink): workload-account metrics/logs/traces            │
 │ EventBridge bus "ai-observability" ← CloudWatch alarm state changes, Alertmanager (via SNS→Lambda) │
 │   → Step Functions: model | data | genai | governance remediation (+ DynamoDB lock/cooldown/audit)  │
 │   → ITSM Lambda → PagerDuty / ServiceNow                                                           │
 └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
 ┌──────────────────────── Security / log-archive account ───────────────────────────────────────────┐
 │ Org CloudTrail (multi-region) · Config aggregator + conformance packs · Security Hub (delegated    │
 │ admin) · GuardDuty · Macie · findings → EventBridge → observability bus (cross-account)            │
 └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Key design decisions

| ADR | Decision | Rationale | Alternative rejected |
|---|---|---|---|
| ADR-1 | **Two-tier OTel gateway**: tier 1 is stateless (redact, validate, spanmetrics, load-balance by trace ID); tier 2 is stateful (tail sampling) | Required for correct tail sampling (A2) and accurate RED metrics (A3) at 500k events/s | A single gateway tier |
| ADR-2 | **Resource identity is set at the source** (agent tier and SDK). The gateway never detects resources for forwarded data. | Fixes multi-cloud attribution (A1) | Gateway-side `resourcedetection` |
| ADR-3 | **One system of record per signal.** Runtime metrics → AMP. ML, data, and RAG quality metrics → CloudWatch (alarms are native EventBridge sources). Traces and app logs → Observe (OD-1). Audit and AWS service logs → CloudWatch Logs or S3. | Removes double ingest cost and the CloudWatch-vs-Prometheus mismatch (A4, A5) | Dual-writing everything |
| ADR-4 | **The telemetry contract is code**: a versioned YAML of metric names, units, labels, and required attributes. It generates the Python SDK constants, OTel processor configs, alert rules, and dashboards, and CI validates against it. | Prevents name drift between emitters and alerts (G9) | Conventions documented only in prose |
| ADR-5 | **Cross-account access through CloudWatch cross-account observability (OAM)** for AWS-native signals, and AMP remote write through IAM role assumption | Native, no data copy, and works in AMG | Per-account dashboards |
| ADR-6 | **Event-driven remediation framework**: every trigger is normalised onto one EventBridge bus and routed by rule to a domain state machine with shared idempotency, cooldown, approval-tier, and audit steps | One Choice-on-`alarmName` (guide pattern) can't handle Macie, GuardDuty, or Config events, and has no safety controls (G7, G18) | A single monolithic state machine |
| ADR-7 | **Runtime routing and safety switches through AWS AppConfig** feature flags, with validators and a deployment strategy | Apps read flags with caching, changes are audited and can be rolled back, and remediation becomes a flag flip (G14) | SSM Parameter written by a Lambda |
| ADR-8 | **Terraform** for all infrastructure (consistent with `model-training-serving`) and **Helm** for collectors | Matches the repository's other implementation | CDK |
| ADR-9 | **Quality evaluation is sampled and asynchronous** (judge LLM, SHAP, ground-truth joins), never in the request path | Protects the TTFT and p99 SLAs and the $/query budget | Inline evaluation |

---

## 5. Telemetry Contract

`contract/telemetry.yaml` is the single source of truth (ADR-4). It contains the following.

**Required resource attributes.** Every signal carries `service.name`, `service.version`, `deployment.environment`, `cloud.provider`, `cloud.region`, `cloud.account.id`, and `k8s.cluster.name` (where applicable), plus `team` and `department`.

**Required span attributes:**

| Domain | Attributes |
|---|---|
| GenAI | `gen_ai.system`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.operation.name`, `tenant_id`, `session_id` |
| Predictive | `prediction_id`, `model.name`, `model.version`, `tenant_id` |
| Retrieval | `db.system=opensearch`, `retrieval.top_k`, `retrieval.index`, `retrieval.latency_ms` |
| Agent | `agent.name`, `agent.iteration`, `tool.name`, `tool.status` |

**Metric names:**

| Metric | Type, unit | Allowed labels |
|---|---|---|
| `gen_ai.client.operation.duration` | histogram, s | `gen_ai.system`, `gen_ai.request.model`, `department`, `cloud.provider` |
| `gen_ai.client.time_to_first_token` | histogram, s | same |
| `gen_ai.client.time_per_output_token` | histogram, s | same |
| `gen_ai.client.token.usage` | histogram, tokens | + `gen_ai.token.type` |
| `gen_ai.client.cost` | counter, USD | `department`, `gen_ai.request.model` |
| `rag.request.duration` | histogram, s | `department`, `route_mode` |
| `rag.quality.{groundedness,context_precision,context_recall}` | gauge (CloudWatch) | `department`, `index` |
| `guardrail.interventions` | counter | `policy` (`PROMPT_ATTACK`, `HATE`, …), `action` |
| `agent.tool.calls` / `agent.tool.failures` / `agent.iterations` | counter / counter / histogram | `agent.name`, `tool.name` |
| `ml.prediction.latency` | histogram, s | `model.name`, `model.version` |
| `ml.quality.{accuracy,precision,recall,f1,auc,ece}`, `ml.shap.rank_shift` | gauge (CloudWatch) | `model.name`, `model.version` |
| `data.quality.{failed_rules,freshness_minutes,row_count}`, `data.drift.psi` | gauge (CloudWatch) | `dataset`, `feature` (bounded set) |

**Cardinality rules (G19):**
* Forbidden as metric labels: `prediction_id`, `session_id`, `user_id`, `trace_id`, raw prompts, URLs with IDs.
* At most 10k active series per metric. The gateway drops and counts violations (`otelcol_contract_violations_total`).

**Redaction set (G1).** Applied to span attributes, span events, log bodies, and log attributes:
* SSN `\b\d{3}-\d{2}-\d{4}\b`
* PAN 13–19 digits, Luhn-checked
* email
* AWS access key `AKIA[0-9A-Z]{16}`
* AWS secret (40-char base64 near `aws_secret`)
* `sk-[A-Za-z0-9]{20,}`
* JWT `eyJ[\w-]+\.[\w-]+\.[\w-]+`
* phone (E.164)

---

## 6. Component Specifications

### 6.1 Telemetry pipeline (M1)

| Tier | Runs as | Processors and connectors | Sizing (initial, then load-tested) |
|---|---|---|---|
| Agent (AWS EKS) | ADOT add-on DaemonSet | `resourcedetection(env, eks, ec2)`, `k8sattributes`, `memory_limiter`, `redaction` (first pass), Prometheus receiver (DCGM, node exporter, kube-state-metrics via Kubernetes service discovery, 15 s), `batch` | 200m CPU / 400 Mi per node |
| Agent (Lambda / ECS) | ADOT Lambda layer / ECS sidecar | same minus scraping | — |
| Agent (Azure / GCP / on-prem) | OTel Collector contrib DaemonSet | `resourcedetection(azure \| gcp \| system)`, `redaction`, mTLS OTLP exporter with persistent queue | — |
| Gateway T1 | Deployment + HPA behind an internal NLB, 3 AZs | `memory_limiter` → contract validation (`filter` / `transform`) → `redaction` (enforced) → cardinality guard (`attributes` delete on metrics) → `spanmetrics` connector → `loadbalancing` exporter (by `traceID`, `k8s` resolver) | 6–30 pods × 2 vCPU |
| Gateway T2 | StatefulSet + headless service | `tail_sampling` (`status_code` ERROR, `numeric_attribute` 5xx, `latency` > 2500 ms, `probabilistic` 5%) → `batch` → exporters with `file_storage` persistent queues | 6–20 pods × 4 vCPU / 8 Gi; `decision_wait` 10 s; `num_traces` sized from QPS × wait |

Sizing approach: load-test with `telemetrygen` at 1×, 2×, and 3× of 500k events/s ([§8](#8-test-and-fault-injection-strategy)). The collectors' own metrics go to AMP, with alerts on `otelcol_exporter_send_failed_*`, queue size, and `otelcol_processor_refused_*`.

### 6.2 Infrastructure observability (M2)

* **GPU:** DCGM exporter DaemonSet on GPU node pools, on-premises included. Alerts:
  * VRAM > 90% for 3 minutes
  * temperature > 85 °C
  * power at the cap for 10 minutes
  * XID errors > 0
  * GPU utilisation < 20% for 6 hours, as a cost alert
* **Kubernetes:** kube-state-metrics and node exporter. Alerts on CrashLoopBackOff (fixes the Part 1 `rate × 300` expression with `increase(...[10m]) > 3`), CPU throttling, OOM kills, node NotReady, and PVC pressure.
* **Lambda, ECS, SageMaker:** CloudWatch metrics through OAM. Alarms on throttles, errors, concurrent executions near the account limit, endpoint `ModelLatency` (µs), and invocation 5XX.
* **Streaming:** MSK and Kinesis consumer lag (`IteratorAgeMilliseconds`, `SumOffsetLag`), because lag delays ground truth and drift detection.

### 6.3 Data and feature observability (M3)

| Check | Implementation | Threshold → action |
|---|---|---|
| Freshness | Glue DQ `DataFreshness`, plus EventBridge "no object in N min" check per prefix | > 30 min → alert |
| Volume | Glue DQ `RowCount` with anomaly detection (or ±20% against a 7-day same-hour median) | ±20% → alert; ±50% → quarantine partition |
| Completeness and validity | Glue DQ rulesets (ported from the Part 2 Deequ checks), parameterised by partition | Any `Error`-level rule fails → quarantine plus data state machine |
| Schema | Glue Schema Registry (Avro/JSON, BACKWARD compatibility) on Kinesis and MSK producers; a Glue crawler diff for S3 | Incompatible registration → producer rejected; alert |
| Drift | PSI job (numeric deciles and categorical shares, minimum 1k rows per window) on Feature Store offline, or capture, against the training baseline. Plus SageMaker Model Monitor data quality where already in use. | PSI ≥ 0.10 warn; ≥ 0.25 → data state machine → retrain pipeline |
| PII | Macie automated discovery plus scheduled jobs on raw and curated buckets | Finding on curated or feature buckets → governance state machine quarantine |

### 6.4 Model performance observability (M4)

* **Prediction logging:**
  * Serving emits `{prediction_id, model, version, ts, features_hash, score, decision}` to Kinesis or MSK. It's asynchronous and non-blocking, through a local agent buffer.
  * Firehose writes it to Parquet, partitioned by `model/version/dt/hour`.
  * Low-QPS models (churn) may keep SageMaker data capture instead (OD-4).
* **Ground truth:**
  * Labels arrive through SQS (with a DLQ). The join runs as a Flink or Glue streaming job, keyed by `prediction_id`, with a late-arrival window per model. Fraud chargebacks can arrive up to 90 days later, and churn labels about 90 days later.
  * Unmatched labels go to a retry queue with exponential backoff. They're never dropped (fixes G5).
* **Evaluator:**
  * A scheduled SageMaker Processing job per model.
  * Metrics: accuracy, precision, recall, F1, AUC, the corrected ECE (G6), and PR-AUC.
  * Statistical floor: each metric is published only when the window has ≥ N labelled samples and ≥ M positives (from config). Below that, publish `ml.quality.insufficient_samples`.
* **SHAP rank shift:** a weekly Clarify or SHAP job on a 5k sample, comparing the top-10 feature ranks with the baseline. The metric is the maximum rank shift; > 2 → evaluation ticket.
* **Per-model SLO files** (`slo/models/<model>.yaml`) hold the thresholds, sample floors, label delay, and the remediation policy (rollback, retrain, or notify).
* **Pilot:** onboard `customer-churn-prod` from [`../model-training-serving/customer-churn-mlops`](../model-training-serving/customer-churn-mlops). It already publishes `MeanPredictedChurnRate` and has a ground-truth merge.

### 6.5 GenAI, RAG, and agent observability (M5)

* **Instrumentation library** (`obs-genai`, Python): a streaming wrapper over Bedrock `ConverseStream` (and the Azure OpenAI or Vertex adapters). It records TTFT, TPOT, token usage, cost (from the pricing config), and guardrail trace results. Retrieval spans come from OpenSearch, and LangGraph is covered by callbacks (tool spans, iteration histogram). Payloads are recorded as span events: they're redacted at the source, then by the gateway.
* **Payload store:** Observe or Firehose → S3 `genai-payloads/` (KMS, 30-day expiry, access through Lake Formation only). This replaces the synchronous `put_object` (G10).
* **Evaluator:**
  * EventBridge Scheduler (every 5 minutes) → Lambda or Step Functions Map over sampled sessions.
  * The judge model comes from config. Output is schema-validated JSON with one retry (G11).
  * It scores groundedness and context precision, and publishes CloudWatch metrics per `department` and `index`.
  * **Context recall** is scored nightly on a curated golden set (≥ 200 Q/A with reference answers) per index.
  * **Judge calibration:** quarterly agreement check against 100 human-labelled samples (target Cohen's κ ≥ 0.6).
* **Guardrails (G12):**
  * Content filters: `PROMPT_ATTACK` (input HIGH), `HATE`, `VIOLENCE`, `SEXUAL`, `INSULTS`, `MISCONDUCT`.
  * PII: anonymise email and phone; block PAN and SSN.
  * Contextual grounding: blocking at 0.70 grounding and 0.70 relevance.
  * A versioned guardrail with trace enabled, so interventions become `guardrail.interventions` metrics.
* **Session denylist:** a DynamoDB table with TTL, checked by the API layer. Written by the genai state machine on prompt-attack interventions above a per-session threshold.
* **Cost:**
  * Bedrock **application inference profiles** per department carry cost allocation tags, so the CUR shows true per-department cost.
  * Real-time `gen_ai.client.cost` drives the $500 soft and $1,000 hard daily alerts. The daily CUR reconciliation flags estimator error over 5%.

### 6.6 SLOs and alerting

| SLO | SLI | Objective | Alerting |
|---|---|---|---|
| RAG availability | Non-5xx RAG responses / all | 99.99% (28 days) | Burn rate 14.4× over 1 h **and** 5 min → page; 6× over 6 h **and** 30 min → page; 1× over 3 days → ticket |
| RAG latency | Requests with root span < 1.5 s | 95% | Burn rate as above |
| TTFT / TPOT | `gen_ai.client.time_to_first_token` p95 < 300 ms; TPOT p95 < 30 ms | 99% of 5-minute windows | p95 breach 10 minutes → page |
| Fraud latency | `ml.prediction.latency` p99 < 10 ms | 99.9% of 1-minute windows | 5 minutes → page |
| Telemetry pipeline | Spans and metrics accepted / received at the gateway | 99.9% | Send-failure or refusal rate > 0.1% for 10 minutes → page the observability on-call |

Every alert has an owner, severity, runbook URL, and dashboard link, and these are validated by CI against the contract. All alerts route through the ITSM Lambda: PagerDuty for P1/P2, ServiceNow for every incident, Slack for warnings.

### 6.7 Closed-loop remediation

| Trigger (spec section 5) | Detection | State machine | Action | Safety controls |
|---|---|---|---|---|
| Recall < model SLO (85% default) | CloudWatch `ml.quality.recall` (sample floor met) | `remediate-model` | Resolve the previous Approved package → blue/green endpoint update → verify → notify | Lock per endpoint; one auto-rollback per 24 h; skip if the previous version is also below the SLO on the same window; afterwards page |
| PSI ≥ 0.25 | CloudWatch `data.drift.psi` | `remediate-data` | Start the SageMaker retraining pipeline with the drift report attached | One run per model per 7 days; quarantine first if a data-quality rule also failed |
| Groundedness < 0.70 | CloudWatch `rag.quality.groundedness` (≥ 50 samples) | `remediate-genai` | AppConfig `route_mode=STRICT_GROUNDING`; auto-revert after 2 h healthy | Revert only on recovery; a manual override flag wins |
| Spend > $1,000/day per department | `gen_ai.client.cost` daily sum by department | `remediate-genai` | AppConfig `route_mode=COST_OPTIMIZED` for non-critical routes of that department | Critical routes are exempt (config); resets at 00:00 UTC |
| Prompt injection | Guardrail `PROMPT_ATTACK` intervention event | `remediate-genai` | Add the session to the denylist; sanitise the response; page the SOC (PagerDuty + ServiceNow security incident) | Threshold per session (≥ 2 in 10 minutes) to avoid denying on one false positive |
| Unmasked PII in a curated or feature bucket | Macie finding (EventBridge) | `remediate-governance` | Deny-tag and bucket-policy quarantine of the object prefix; notify the data owner and SOC | Read access is never removed for security; reversible |
| Unauthorised model change | CloudTrail → EventBridge on SageMaker mutate APIs by a principal not in the pipeline-role allowlist | `remediate-governance` | Snapshot, then propose rollback and propose IAM restriction | **Human approval** (Step Functions task token through Slack or ServiceNow) before any IAM change (OD-6) |

Every state machine starts with the same shared steps: `NormaliseEvent → AcquireLock (DynamoDB conditional put, TTL) → CheckCooldown → CheckKillSwitch (AppConfig) → …`. Every run ends by writing to the remediation audit table and posting to ITSM.

### 6.8 Dashboards (AMG, provisioned from code)

1. **Executive FinOps and ROI:**
   * spend per minute and per day by department, provider, and model
   * cost per RAG query against the $0.015 target
   * daily ROI from Athena (CUR + outcomes, G16)
   * budget burn
2. **Predictive ML and feature quality:** quality metrics per model and version against the SLO, ECE reliability diagram, PSI heatmap, SHAP rank shift, label coverage and delay.
3. **GenAI and RAG quality:** groundedness and context precision/recall, TTFT/TPOT/E2E percentiles, guardrail interventions by policy, route mode timeline, agent tool failures and iterations.
4. **SRE and compute:** GPU (DCGM), pods and nodes, Lambda, endpoints, stream lag, and **telemetry pipeline health** (gateway throughput, queue, refusals, sampling ratio, contract violations).
5. **SLO and error budgets:** one row per SLO, plus the remediation activity log.

---

## 7. Milestone Plan

Roles:

| Abbreviation | Role |
|---|---|
| **OBS** | Observability/SRE engineer (2 people) |
| **MLE** | ML engineer |
| **GAI** | GenAI engineer |
| **SEC** | Security engineer |
| **FIN** | FinOps analyst (part-time) |

Estimates are in engineer-weeks.

| Milestone | Guide part | Owner | Estimate | Depends on |
|---|---|---|---|---|
| M0 Foundations: accounts, OAM, AMP/AMG/Observe tenancy, contract v1, Terraform skeleton, decisions OD-1…OD-9 | Part 6 | OBS + SEC | 3 | — |
| M1 Telemetry pipeline: agents, two-tier gateway, redaction, sampling, load test | Parts 1, 6 | OBS | 5 | M0 |
| M2 Infrastructure observability | Part 1 | OBS | 2 | M1 |
| M3 Data and feature observability | Part 2 | MLE | 3 | M0 (M7 for actions) |
| M4 Model performance observability | Part 3 | MLE | 4 | M1, M3 |
| M5 GenAI, RAG, and agent observability | Part 4 | GAI | 5 | M1 |
| M6 Governance, security, FinOps, ITSM | Part 5 | SEC + FIN | 4 | M0 |
| M7 Remediation framework and five playbooks | Parts 3–5 | OBS + MLE + GAI | 4 | M3–M6 detections |
| M8 Multi-cloud federation (Azure, GCP, on-prem) | Part 6 | OBS | 3 | M1 |
| M9 SLOs, dashboards, game days, acceptance | Part 6 | All | 3 | M2–M8 |
| **Total** | | | **~36 engineer-weeks**, about **12 weeks** for a team of 6 | |

```text
Week:      1  2  3  4  5  6  7  8  9 10 11 12
M0        ███
M1           █████████
M2                    ███
M3           ██████
M4                    ███████
M5                    █████████
M6           ███████
M7                             ███████
M8                       ██████
M9                                      █████
```

**Critical path:** M0 → M1 → M5 → M7 → M9.

### M0: Foundations

**Tasks**

1. AWS Organizations layout: workload accounts, an **observability** account, and a **security/log-archive** account. CloudWatch cross-account observability (OAM sink in observability, links from workload accounts).
2. AMP workspace, AMG workspace (IAM Identity Center SSO, teams for SRE, MLOps, GenAI, Security, and Finance), Observe tenancy with ingest tokens in Secrets Manager.
3. Write telemetry contract v1 ([§5](#5-telemetry-contract)) and its generator (SDK constants, collector processor snippets, alert rule skeletons). The CI validator rejects unknown metric names and forbidden labels.
4. Terraform repository layout and remote state per account. Fix the A8 links.
5. Resolve OD-1 to OD-9 ([§12](#12-risks-and-open-decisions)).

**Exit criteria:** an AMG data source works for AMP, CloudWatch (cross-account), and Observe; the contract CI runs on PRs; every OD has an owner and date.

### M1: Telemetry pipeline (fixes A1–A3, G1, G19, G20)

**Tasks**

1. Agent tier through the ADOT EKS add-on (agent config from contract templates), the ADOT Lambda layer, and ECS sidecars.
2. Gateway T1 and T2 Helm releases (otelcol-contrib, pinned version) on a dedicated EKS cluster in the observability account, behind an internal NLB with PrivateLink endpoints shared to workload VPCs.
3. Redaction (agent and gateway), contract validation, cardinality guard, `spanmetrics`, and tail-sampling policies. Persistent queues (`file_storage` on EBS gp3).
4. **PII canary:** a synthetic service emits a span, event, and log containing SSN, PAN, AWS key, and JWT every minute. A scheduled Observe query and an AMP label check fail the canary if any raw value is found.
5. **Load test** with `telemetrygen`: 500k, 1M, and 1.5M events/s for 30 minutes each. Record CPU, memory, latency, and drops. Fix HPA targets and T2 `num_traces`.

**Exit criteria:**
* 0 raw PII values in 24 h of canary traffic
* < 0.1% refused or dropped at 1.5× peak
* trace completeness ≥ 99.5% for sampled traces (all spans present)
* spanmetrics request counts within 1% of the source counts

### M2: Infrastructure observability (Part 1, G2)

**Tasks**

1. DCGM exporter and node exporter on GPU pools.
2. kube-state-metrics.
3. Alert rules from [§6.2](#62-infrastructure-observability-m2), with the corrected crash-loop expression.
4. OAM-based alarms for Lambda, ECS, and SageMaker, and stream lag.
5. The IRSA role from Part 1, narrowed to the AMP workspace ARN (not `workspace/*`).

**Exit criteria:** every Part 1 alert fires in a fault test (GPU stress via `dcgmproftester`, crash-looping pod, Lambda throttle), and the SRE dashboard is live.

### M3: Data and feature observability (Part 2, G3, G4)

**Tasks**

1. Glue DQ rulesets per dataset (ported Deequ checks, plus freshness and volume).
2. Schema Registry for Kinesis and MSK producers.
3. Macie discovery jobs.
4. PSI job: numeric and categorical, with sample floors, unit-tested against the closed-form PSI of two known distributions.
5. Quarantine prefix convention and partition-level quarantine through a Glue DQ result handler.

**Exit criteria:** an injected schema break, stale partition, ±50% volume, and shifted feature are each detected within one evaluation window, and the corresponding metric is visible in AMG.

### M4: Model performance observability (Part 3, A7, G5, G6, G8, G21)

**Tasks**

1. Prediction-event schema in the contract. Kinesis or MSK stream and Firehose to Parquet.
2. Serving-side async emitter (Triton ensemble post-processor or app middleware).
3. Ground-truth SQS, join job, and retry and DLQ handling.
4. Evaluator Processing job with the corrected ECE and sample floors. Per-model SLO files.
5. SHAP rank-shift job.
6. Pilot on `customer-churn-prod`, then fraud and credit risk.

**Exit criteria:**
* Label join completeness ≥ 99% for labels arriving within the window.
* ECE unit tests pass against reference values.
* Degraded predictions injected for the pilot model produce a recall alarm with the correct `model.version` dimension.
* Fraud serving p99 measured at < 10 ms with the async emitter on (OD-3 platform).

### M5: GenAI, RAG, and agents (Part 4, G9–G15)

**Tasks**

1. `obs-genai` library: streaming TTFT/TPOT, token usage, cost, guardrail trace, OpenSearch retrieval spans, LangGraph tool and iteration callbacks. Contract tests.
2. Async payload store through span events and Firehose.
3. Evaluator (sampled judge, fixed parsing) and the golden-set context-recall job. Judge-human agreement check.
4. Guardrail Terraform with `PROMPT_ATTACK`, messaging, and version.
5. Application inference profiles per department.
6. AppConfig routing-mode flag read by the RAG service. Session denylist check.

**Exit criteria:**
* TTFT and TPOT match an independent client-side stopwatch within 5%.
* A hallucination test set (answers contradicting context) drives groundedness below 0.70.
* A jailbreak and prompt-injection corpus produces guardrail interventions ≥ 95% of the time.
* Measured cost per RAG query is ≤ $0.015 including judge sampling.

### M6: Governance, security, FinOps, ITSM (Part 5, G16–G18)

**Tasks**

1. Organization CloudTrail (multi-region, log-file validation, S3 Object Lock in log-archive).
2. Config aggregator and conformance packs (Operational Best Practices for AI/ML, plus custom rules: SageMaker endpoints with KMS and data capture, Bedrock invocation logging enabled).
3. Security Hub and GuardDuty (delegated admin), with findings forwarded to the observability bus.
4. CloudTrail-based model-change detection.
5. ITSM Lambda: PagerDuty Events v2 with dedup and resolve, ServiceNow Table API, Secrets Manager, DLQ.
6. CUR 2.0 → Athena. Daily ROI and cost-per-inference views with the business-outcome table contract (owner: FIN).

**Exit criteria:** a test Macie finding, GuardDuty sample finding, and unauthorised `UpdateEndpoint` each create exactly one ServiceNow incident and one PagerDuty incident, and both auto-resolve when cleared.

### M7: Remediation framework (G3, G7, G14, G18; [§6.7](#67-closed-loop-remediation))

**Tasks**

1. Observability EventBridge bus, cross-account rules, and the Alertmanager → SNS → normaliser Lambda.
2. Shared steps: lock, cooldown, kill switch, audit, ITSM.
3. Four domain state machines with the seven playbooks.
4. Human-approval task-token flow (Slack interactive message or ServiceNow approval).
5. A global kill switch and a dry-run mode per playbook.

**Exit criteria:** each of the seven playbooks passes its fault-injection test ([§8](#8-test-and-fault-injection-strategy)) in dry-run and then live in staging; a second trigger inside the cooldown is suppressed and audited.

### M8: Multi-cloud federation (Part 6)

**Tasks**

1. Network paths: Site-to-Site VPN or Direct Connect for on-premises, and VPN or Interconnect for Azure and GCP (OD-7). mTLS OTLP endpoint on the T1 NLB as fallback.
2. Agents in AKS and GKE, and on the bare-metal GPU cluster (DCGM).
3. Azure OpenAI and Vertex adapters in `obs-genai`.
4. Cross-cloud cost ingestion (Azure Cost Management export and GCP billing export → S3 → Athena) for the FinOps dashboard.

**Exit criteria:** telemetry from each environment carries the correct `cloud.provider` and `cloud.region` (A1); a cross-cloud RAG trace (AWS retrieval → Azure OpenAI fallback) is visible end to end in Observe.

### M9: SLOs, dashboards, game days, acceptance

**Tasks**

1. SLO definitions and burn-rate rules generated from the contract.
2. The five dashboards provisioned through the Grafana Terraform provider.
3. Runbooks per alert.
4. Two game days: (a) a gateway T2 zone failure plus 2× traffic, and (b) the combined fault-injection suite.
5. Acceptance ([§9](#9-acceptance-test-plan)).

**Exit criteria:** all acceptance tests pass; on-call rotation is staffed; error budgets are reported weekly.

---

## 8. Test and Fault-Injection Strategy

Part 6 §15 names three fault-injection scripts, but none exist; this plan builds them in `fault-injection/`.

| Script | Injects | Expected outcome |
|---|---|---|
| `inject_pii_canary.py` | SSN, PAN, AWS key, and JWT in span attributes, events, log body, and log attributes | No raw value in Observe, AMP, or CloudWatch; canary metric stays at 0 |
| `inject_feature_drift.py` | Shifted numeric and categorical features into the serving stream | PSI ≥ 0.25 → `remediate-data` → retraining started (dry-run first) |
| `inject_degraded_predictions.py` | Flipped labels for the pilot model in the ground-truth stream | Recall alarm → `remediate-model` → rollback to the previous Approved version |
| `test_rag_hallucination.py` | Q/A pairs whose answers contradict retrieved context | Groundedness < 0.70 → `STRICT_GROUNDING` flag → auto-revert after recovery |
| `test_prompt_injection.py` | OWASP LLM01 corpus (direct and indirect injection) | Guardrail interventions, session denylisted, SOC incident created |
| `simulate_budget_overrun.py` | Synthetic cost metric above $1,000 for one department | `COST_OPTIMIZED` for that department only; others unchanged |
| `simulate_model_tamper.sh` | `UpdateEndpoint` from a non-pipeline role in staging | Governance state machine waits for approval; ITSM incidents created |
| `telemetrygen` load profiles | 500k–1.5M events/s | Pipeline SLO met; no PII; sampling ratios as configured |
| Chaos (Litmus or AWS FIS) | Kill a gateway T2 AZ; throttle the AMP remote-write role | No data loss beyond queue capacity; pipeline-health alert fires |

Unit tests cover the ECE and PSI maths, judge parsing, cost calculation, contract validators, and every Lambda (botocore Stubber). Integration tests run collector configs in Docker (`otelcol-contrib --config` validation plus a golden input/output pipeline test). State machines are tested with Step Functions Local or TestState mocks.

---

## 9. Acceptance Test Plan

| # | Test | Expected result | Milestone |
|---|---|---|---|
| AT-1 | Load test at 1.5× peak (750k events/s) | < 0.1% loss, gateway p99 added latency < 50 ms | M1 |
| AT-2 | PII canary for 24 h | 0 raw values in any sink | M1 |
| AT-3 | Trace attributes | 100% of sampled spans carry the required attributes from [§5](#5-telemetry-contract) | M1, M8 |
| AT-4 | GPU, pod, and Lambda faults | Part 1 alerts fire with runbook links | M2 |
| AT-5 | Data faults (schema, freshness, volume, drift, PII) | Detected in one window; PSI drift starts retraining | M3, M7 |
| AT-6 | Degraded pilot model | Recall alarm → automatic rollback to the previous Approved version within 15 minutes of the alarm | M4, M7 |
| AT-7 | Hallucination set | Groundedness < 0.70 → strict grounding mode → auto-revert | M5, M7 |
| AT-8 | Prompt-injection corpus | ≥ 95% intervention rate; session denylisted; SOC incident | M5, M7 |
| AT-9 | Budget overrun | Cost routing for one department only; finance notified | M5, M7 |
| AT-10 | Unauthorised model change | Approval requested; nothing changes until approved; audit record written | M6, M7 |
| AT-11 | Multi-cloud trace | Single trace across AWS and Azure with correct `cloud.*` attributes | M8 |
| AT-12 | SLO burn | Synthetic 5xx at 15× budget pages within 5 minutes; 1× budget opens a ticket | M9 |

---

## 10. Security and Compliance (of the observability platform itself)

* **Encryption:** KMS customer-managed keys for AMP, S3 payload and evaluation buckets, Firehose, DynamoDB, and SNS. TLS 1.2+ on OTLP, mTLS for off-AWS agents.
* **Access:**
  * AMG through IAM Identity Center with team-scoped folders.
  * The GenAI payload bucket is readable only through Lake Formation by the GenAI evaluation role and break-glass.
  * Observe RBAC mirrors the AMG teams.
* **Least privilege:** the IRSA policy is scoped to the workspace ARN (the guide uses `workspace/*`). Remediation roles are per playbook, and only `remediate-governance` may touch IAM, after approval.
* **Retention:**

  | Data | Retention |
  |---|---|
  | Traces | 30 days |
  | Application logs | 30 days hot, 1 year in S3 |
  | Audit (CloudTrail) | 7 years, Object Lock |
  | GenAI payloads | 30 days |
  | Remediation audit | 2 years |

* **Data residency:** EU telemetry stays in an EU gateway and region if required (OD-8). The gateway can route by `cloud.region`.

---

## 11. Cost Management

| Driver | Control |
|---|---|
| Trace volume | Tail sampling (5% baseline); spans to metrics before sampling; drop health-check spans at the agent |
| Metric cardinality | Contract label allowlist; per-metric series limit; weekly top-N cardinality report |
| Log volume | Severity filtering at the agent (DEBUG off in production); CloudWatch Logs only for mandated streams (ADR-3) |
| Prediction logging | Async stream + Parquet instead of 100% capture on high-QPS endpoints (A7) |
| Judge LLM | 5–10% sampling; small judge model; batch scoring |
| GPU metrics | 15 s scrape; drop unused DCGM fields |
| Gateway compute | HPA plus Graviton nodes; Spot for T1 (stateless) only |

Budget: a monthly observability cost target of ≤ 8% of the monitored workloads' run cost, reported on the FinOps dashboard.

---

## 12. Risks and Open Decisions

### 12.1 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A 10 ms p99 at 500k QPS isn't achievable on the chosen serving platform | High | High | OD-3 decided in M0; latency budget measured in M4 before onboarding fraud |
| Tail-sampling memory blow-up at peak | Medium | High | T2 sizing from the load test; `memory_limiter`; persistent queues; alert on dropped traces |
| PII leaks through a new attribute | Medium | High | Two-tier redaction; canary; contract CI; Observe sensitive-data scanning |
| Judge LLM disagrees with humans, causing false remediations | Medium | Medium | κ check; sample floor; groundedness remediation only auto-reverts, never changes data |
| Automated rollback loops during genuine drift | Medium | High | Cooldown, previous-version check, escalation (G7) |
| Ground-truth delay (up to 90 days) hides decay | High | Medium | Leading indicators: PSI, prediction distribution, SHAP rank shift |
| Multi-cloud network paths delayed | Medium | Medium | mTLS public OTLP fallback; M8 off the critical path |
| Observability cost overrun | Medium | Medium | [§11](#11-cost-management) controls; monthly review |

### 12.2 Open decisions (resolve in M0)

| ID | Decision | Default if undecided |
|---|---|---|
| OD-1 | System of record for traces and app logs: Observe, or X-Ray plus CloudWatch Logs | Observe (spec §2 and Part 6); X-Ray off; CloudWatch Logs for AWS-native and audit only |
| OD-2 | Dashboards: AMG or Grafana Enterprise | AMG |
| OD-3 | Fraud serving platform for 10 ms / 500k QPS | Triton on EKS (GPU or CPU per model), with SageMaker for lower-QPS models |
| OD-4 | Data capture / prediction logging rate per model | 100% async stream for every model; SageMaker capture 100% for QPS < 100 and ≤ 5% above |
| OD-5 | Judge sampling rate and model | 10% and every flagged session; smallest model with κ ≥ 0.6 |
| OD-6 | Remediation autonomy | Automatic: rollback, retrain, routing flags, session denylist, PII quarantine. Approval: IAM changes, cross-account actions. |
| OD-7 | Multi-cloud connectivity | VPN now, Direct Connect / Interconnect later |
| OD-8 | Data residency for EU telemetry | Single us-west-2 hub unless legal requires EU; the gateway supports a regional split |
| OD-9 | IaC | Terraform plus Helm (ADR-8) |

---

## 13. Deliverables Traceability

| Spec item | Delivered by |
|---|---|
| §2 service mapping (agents, TSDB, logs/traces, dashboards) | M0, M1, M9 |
| §3 SLAs (availability, TTFT, TPOT, E2E, 10 ms, throughput, cost) | M1, M4, M5, M9 (SLOs) |
| §4A infrastructure | M2 |
| §4B data and features | M3 |
| §4C model performance | M4 |
| §4D GenAI, RAG, safety, agents | M5 |
| §4E tracing, sampling, PII | M1, M8 |
| §5 audit and security | M6 |
| §5 closed-loop remediation (five responses) | M7 |

---

## 14. Backlog

1. QuickSight executive pack on the CUR and ROI datasets
2. Anomaly-detection alerts (CloudWatch anomaly detection or AMP recording rules with seasonal baselines) for token spend and volume
3. Automatic baselining of SLO thresholds per model from historical windows
4. LLM-judge drift monitoring (judge score distribution against the golden set over time)
5. eBPF-based network observability for GPU nodes (Cilium/Hubble or Pixie)
