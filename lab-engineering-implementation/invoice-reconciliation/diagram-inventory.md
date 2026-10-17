# Draw.io inventory: `architecture.drawio`

Pages: 10

| Page | Components | Edges | Icons | Issues |
|---|---:|---:|---:|---|
| 1 Logical Architecture | 35 | 22 | 15 | 0 |
| 2 Infrastructure | 32 | 10 | 0 | 0 |
| 3 Security | 30 | 8 | 16 | 0 |
| 4 Observability | 21 | 8 | 7 | 0 |
| 5 CI-CD & MLOps | 21 | 15 | 3 | 0 |
| 6 Data Lineage & Privacy | 21 | 15 | 4 | 0 |
| 7 Resilience & Fallback | 22 | 11 | 8 | 0 |
| 8 Workflow Orchestration | 29 | 20 | 1 | 1 |
| 9 FinOps | 22 | 8 | 7 | 0 |
| 10 Governance & HITL | 23 | 13 | 0 | 1 |

## 1 Logical Architecture (1 · Logical Architecture: Invoice-to-PO Reconciliation)

**👥 USER & SOURCE LAYER**

- 📁 Google Drive folders (invoices, POs) _(component)_
- 🧑‍💼 AP Analyst (exception review) _(component)_
- 🧑‍🔧 Procurement / Controller _(component)_
- 🔍 Internal Audit _(component)_
- 🏢 Downstream backend / ERP _(component)_

**🌐 APPLICATION & API LAYER**

- 🔎 Drive Watcher (changes API) _(component)_ `aws:lambda`
- 📬 Intake Queue + DLQ _(component)_ `aws:sqs`
- 🚪 Existing Backend API _(component)_ `aws:api_gateway`
- 🛡️ WAF + Auth (OIDC) _(component)_ `aws:waf`

**⚙️ ORCHESTRATION**

- 🔀 Step Functions (per-doc workflow) _(component)_ `aws:step_functions`
- 🔑 Idempotency guard (doc hash + rule ver) _(database)_
- ♻️ Retry / backoff / DLQ redrive _(component)_
- ⚠️ Exception router → review queue _(component)_

**🧠 AI / ML & RULES LAYER**

- 🏷️ Doc classifier (inv/PO/credit) _(component)_
- 📄 Textract AnalyzeExpense _(component)_ `aws:textract`
- 🤖 Bedrock multimodal verifier _(component)_ `aws:bedrock`
- 🔗 PO identification (deterministic) _(component)_
- 📐 Line matcher (embed + Hungarian) _(component)_
- 🧮 Rules engine (Decimal, tolerances) _(component)_ `aws:fargate`
- 🔁 Duplicate / repeated-billing _(component)_
- 🚨 Risk scorer (IsoForest→LightGBM) _(component)_ `aws:sagemaker`

**🗄️ DATA LAYER**

- Raw documents (S3, immutable) _(database)_
- Evidence store (S3 Object Lock) _(database)_
- Results & anomalies (Aurora PG) _(database)_
- PO / supplier master cache _(database)_
- Policy & tolerance versions _(database)_
- Decision audit log _(database)_

**🔐 SECURITY LAYER**

- 🪪 IAM least-privilege roles _(component)_ `aws:identity_and_access_management`
- 🔑 KMS customer keys _(component)_ `aws:key_management_service`
- 🗝️ Secrets Manager (Drive SA) _(component)_ `aws:secrets_manager`
- 🛑 Bedrock Guardrails / schema check _(component)_ `aws:bedrock`
- 📜 CloudTrail _(component)_ `aws:cloudtrail`

**📈 OPERATIONS & OBSERVABILITY**

- 📊 CloudWatch / Grafana _(component)_ `aws:cloudwatch`
- 🔭 OpenTelemetry traces _(component)_ `aws:xray`
- 📉 Drift & review-rate monitor _(component)_

**Connections**

- 📁 Google Drive folders (invoices, POs) -> 🔎 Drive Watcher (changes API) [Changes API / poll]
- 🔎 Drive Watcher (changes API) -> 📬 Intake Queue + DLQ [File events]
- 📬 Intake Queue + DLQ -> 🔀 Step Functions (per-doc workflow) [Trigger]
- 🔀 Step Functions (per-doc workflow) -> 🔑 Idempotency guard (doc hash + rule ver) [Dedup check]
- 🔀 Step Functions (per-doc workflow) -> 🏷️ Doc classifier (inv/PO/credit) [Classify]
- 🏷️ Doc classifier (inv/PO/credit) -> 📄 Textract AnalyzeExpense [Extract]
- 📄 Textract AnalyzeExpense -> 🤖 Bedrock multimodal verifier [Low-confidence fields]
- 🤖 Bedrock multimodal verifier -> 🔗 PO identification (deterministic) [Validated JSON]
- 🔗 PO identification (deterministic) -> 📐 Line matcher (embed + Hungarian) [Candidate PO]
- 📐 Line matcher (embed + Hungarian) -> 🧮 Rules engine (Decimal, tolerances) [Line pairs]
- 🧮 Rules engine (Decimal, tolerances) -> 🔁 Duplicate / repeated-billing [Result]
- 🔁 Duplicate / repeated-billing -> 🚨 Risk scorer (IsoForest→LightGBM) [Signals]
- 🧮 Rules engine (Decimal, tolerances) -> Results & anomalies (Aurora PG) [Persist outcome]
- 🧮 Rules engine (Decimal, tolerances) -> Evidence store (S3 Object Lock) [Evidence bundle]
- 🔀 Step Functions (per-doc workflow) -> ⚠️ Exception router → review queue [Unsafe / ambiguous]
- ⚠️ Exception router → review queue -> 🧑‍💼 AP Analyst (exception review) [Review queue]
- 🔎 Drive Watcher (changes API) -> Raw documents (S3, immutable) [Copy original]
- 🔗 PO identification (deterministic) -> PO / supplier master cache [Lookup]
- 🧮 Rules engine (Decimal, tolerances) -> Policy & tolerance versions [Policy vN]
- 🚪 Existing Backend API -> Results & anomalies (Aurora PG) [Query results]
- 🏢 Downstream backend / ERP -> 🚪 Existing Backend API [REST (existing contract)]
- 🔍 Internal Audit -> Decision audit log [Evidence trace]

**Components with no connection:** 🧑‍🔧 Procurement / Controller; 🛡️ WAF + Auth (OIDC); ♻️ Retry / backoff / DLQ redrive; 🪪 IAM least-privilege roles; 🔑 KMS customer keys; 🗝️ Secrets Manager (Drive SA); 🛑 Bedrock Guardrails / schema check; 📜 CloudTrail; 📊 CloudWatch / Grafana; 🔭 OpenTelemetry traces; 📉 Drift & review-rate monitor

## 2 Infrastructure (2 · Infrastructure Architecture (AWS, primary region, 2 AZ))

**Region (primary; DR region in Resilience view)**

- Route 53 _(component)_ `aws:route_53`
- WAF _(component)_ `aws:waf`
- API Gateway _(component)_ `aws:api_gateway`
- Cognito _(component)_ `aws:cognito`
- S3 raw _(component)_ `aws:s3`
- S3 evidence _(component)_ `aws:s3`
- SQS + DLQ _(component)_ `aws:sqs`
- Step Functions _(component)_ `aws:step_functions`
- Textract _(component)_ `aws:textract`
- Bedrock _(component)_ `aws:bedrock`
- SageMaker EP _(component)_ `aws:sagemaker`
- KMS _(component)_ `aws:key_management_service`
- CloudWatch _(component)_ `aws:cloudwatch`
- Secrets Mgr _(component)_ `aws:secrets_manager`
- EventBridge _(component)_ `aws:eventbridge_default_bus`
- DynamoDB _(component)_ `aws:dynamodb`

**VPC 10.20.0.0/16**

- Internet GW _(component)_ `aws:internet_gateway`
- Internal ALB _(component)_ `aws:application_load_balancer`
- S3 Gateway EP _(component)_ `aws:endpoints`
- Interface EP (Textract/Bedrock) _(component)_ `aws:endpoints`

**Public subnet**

- NAT Gateway _(component)_ `aws:nat_gateway`
- NAT Gateway _(component)_ `aws:nat_gateway`

**Private app subnet**

- Fargate: API _(component)_ `aws:fargate`
- Fargate: Reconciler _(component)_ `aws:fargate`
- Lambda: Watcher _(component)_ `aws:lambda`
- Fargate: API _(component)_ `aws:fargate`
- Fargate: Reconciler _(component)_ `aws:fargate`
- Lambda: Watcher _(component)_ `aws:lambda`

**Private data subnet**

- Aurora PG (writer) _(component)_ `aws:aurora`
- ElastiCache (cache) _(component)_ `aws:elasticache`
- Aurora PG (reader) _(component)_ `aws:aurora`
- ElastiCache (cache) _(component)_ `aws:elasticache`

**Connections**

- API Gateway -> Internal ALB [HTTPS via VPC Link]
- Internal ALB -> Fargate: API [HTTP]
- Fargate: Reconciler -> Aurora PG (reader) [SQL / TLS]
- Fargate: Reconciler -> Aurora PG (writer) [SQL / TLS]
- Fargate: Reconciler -> S3 Gateway EP [S3 (private)]
- Fargate: Reconciler -> Interface EP (Textract/Bedrock) [Textract / Bedrock]
- NAT Gateway -> Internet GW [Egress (Drive API)]
- Lambda: Watcher -> NAT Gateway [Drive API]
- Route 53 -> WAF [DNS]
- WAF -> API Gateway [Filtered]

**Components with no connection:** Cognito; ElastiCache (cache); NAT Gateway; Fargate: API; Lambda: Watcher; ElastiCache (cache); S3 raw; S3 evidence; SQS + DLQ; Step Functions; Textract; Bedrock; SageMaker EP; KMS; CloudWatch; Secrets Mgr; EventBridge; DynamoDB

**Duplicate labels:** ElastiCache (cache); Fargate: API; Fargate: Reconciler; Lambda: Watcher; NAT Gateway

## 3 Security (3 · Security Architecture & Governance)

**🪪 IDENTITY & ACCESS (TL)**

- Cognito / OIDC SSO _(component)_ `aws:cognito`
- Per-service IAM roles _(component)_ `aws:identity_and_access_management`
- IAM Identity Center (staff) _(component)_ `aws:single_sign_on`
- Drive service account (read-only folders) _(component)_
- RBAC: AP / Procurement / Audit _(component)_
- Secrets Manager rotation _(component)_ `aws:secrets_manager`

**🛑 POLICY & AI GUARDRAILS (TR)**

- WAF managed rules + rate limit _(component)_ `aws:waf`
- Bedrock Guardrails _(component)_ `aws:bedrock`
- Prompt-injection defense: document text = data _(component)_
- Strict JSON schema validation _(component)_
- PII / bank-data redaction in logs _(component)_
- SCPs / permission boundaries _(component)_

**📜 AUDIT & EVIDENCE (BL)**

- CloudTrail (mgmt + data events) _(component)_ `aws:cloudtrail`
- S3 Object Lock evidence _(database)_
- AWS Config rules _(component)_ `aws:config`
- Security Hub _(component)_ `aws:security_hub`
- IAM Access Analyzer _(component)_ `aws:identity_and_access_management`
- Immutable decision log _(database)_

**🚨 THREAT DETECTION & NETWORK (BR)**

- GuardDuty _(component)_ `aws:guardduty`
- Inspector (images, Lambda) _(component)_ `aws:inspector`
- VPC Flow Logs _(component)_ `aws:virtual_private_cloud`
- Private subnets + SGs/NACLs _(component)_
- ECR image scanning + signing _(component)_ `aws:elastic_container_registry`
- Shield Standard _(component)_ `aws:shield`

**🔒 DATA PROTECTION BAR**

- KMS CMKs per data class _(component)_ `aws:key_management_service`
- TLS 1.2+/1.3 in transit _(component)_
- Encryption at rest (S3/Aurora/SQS) _(component)_
- Retention & legal-hold policy _(component)_
- MFA for privileged roles _(component)_
- Macie scan on raw bucket _(component)_ `aws:macie`

**Connections**

- Cognito / OIDC SSO -> Per-service IAM roles [Token → role]
- Drive service account (read-only folders) -> Secrets Manager rotation [Credential]
- WAF managed rules + rate limit -> Bedrock Guardrails [Filtered input]
- Bedrock Guardrails -> Strict JSON schema validation [Model output]
- CloudTrail (mgmt + data events) -> S3 Object Lock evidence [Log archive]
- GuardDuty -> Security Hub [Findings]
- Per-service IAM roles -> KMS CMKs per data class [Key policy]
- RBAC: AP / Procurement / Audit -> Cognito / OIDC SSO [Groups]

**Components with no connection:** IAM Identity Center (staff); Prompt-injection defense: document text = data; PII / bank-data redaction in logs; SCPs / permission boundaries; AWS Config rules; IAM Access Analyzer; Immutable decision log; Inspector (images, Lambda); VPC Flow Logs; Private subnets + SGs/NACLs; ECR image scanning + signing; Shield Standard; TLS 1.2+/1.3 in transit; Encryption at rest (S3/Aurora/SQS); Retention & legal-hold policy; MFA for privileged roles; Macie scan on raw bucket

## 4 Observability (4 · Observability, Logging & Monitoring)

**COLLECTION**

- OTel / ADOT collector _(component)_
- CloudWatch Logs (structured JSON) _(component)_ `aws:cloudwatch`
- X-Ray traces _(component)_ `aws:xray`
- Amazon Managed Prometheus _(component)_
- VPC Flow Logs _(component)_
- Domain events (EventBridge) _(component)_ `aws:eventbridge_default_bus`

**VISUALIZATION**

- Grafana dashboards _(component)_
- CloudWatch dashboards _(component)_ `aws:cloudwatch`
- Athena audit queries _(component)_ `aws:athena`
- QuickSight KPIs (STP, leakage) _(component)_ `aws:quicksight`
- Evidently drift reports _(component)_

**ALERTING**

- CloudWatch alarms _(component)_ `aws:cloudwatch`
- SNS → on-call _(component)_ `aws:sns`
- SLO burn-rate alerts _(component)_
- Budgets & anomaly alerts _(component)_
- Reviewer-override-rate alert _(component)_

**OPERATIONS**

- Runbooks (SSM) _(component)_ `aws:systems_manager`
- DLQ redrive tool _(component)_
- Safe reprocess API _(component)_
- Exception queue age _(component)_
- Post-incident review _(component)_

**Connections**

- OTel / ADOT collector -> Grafana dashboards [Metrics]
- CloudWatch Logs (structured JSON) -> Athena audit queries [Query]
- X-Ray traces -> CloudWatch dashboards [Traces]
- Grafana dashboards -> CloudWatch alarms [Thresholds]
- CloudWatch alarms -> SNS → on-call [Notify]
- SNS → on-call -> Runbooks (SSM) [Page → runbook]
- Evidently drift reports -> Reviewer-override-rate alert [Drift signal]
- Exception queue age -> SLO burn-rate alerts [Age metric]

**Components with no connection:** Amazon Managed Prometheus; VPC Flow Logs; Domain events (EventBridge); QuickSight KPIs (STP, leakage); Budgets & anomaly alerts; DLQ redrive tool; Safe reprocess API; Post-incident review

## 5 CI-CD & MLOps (5 · CI/CD & MLOps Pipeline)

**SOURCE**

- GitHub repo (trunk + PRs) _(component)_
- PR checks / CODEOWNERS _(component)_
- Golden set (S3 + DVC) _(database)_

**CI**

- Lint + type check _(component)_
- Unit + property tests _(component)_
- Golden-set regression GATE _(decision)_
- Trivy / Inspector scan _(component)_

**TRAIN / TUNE**

- Reviewer labels (Ground Truth) _(component)_
- LayoutLMv3 fine-tune (SageMaker) _(component)_ `aws:sagemaker`
- Optuna thresholds _(component)_
- MLflow tracking _(component)_

**REGISTRY**

- Model registry (Exp→Stg→Cand→Prod) _(database)_
- ECR images (signed) _(component)_ `aws:elastic_container_registry`
- Prompt / schema / policy versions _(database)_

**DEPLOY**

- Terraform plan/apply _(component)_
- Shadow mode _(component)_
- Canary by supplier segment _(component)_
- Production _(component)_ `aws:fargate`

**MONITOR**

- Drift (PSI/KS) _(component)_
- Review & override rate _(component)_
- Cost / page _(component)_

**Connections**

- GitHub repo (trunk + PRs) -> Lint + type check [Push]
- PR checks / CODEOWNERS -> Unit + property tests [Trigger]
- Golden set (S3 + DVC) -> Golden-set regression GATE [Eval set]
- Golden-set regression GATE -> Trivy / Inspector scan [Pass]
- Trivy / Inspector scan -> ECR images (signed) [Build & push]
- Reviewer labels (Ground Truth) -> LayoutLMv3 fine-tune (SageMaker) [Training data]
- LayoutLMv3 fine-tune (SageMaker) -> MLflow tracking [Metrics]
- MLflow tracking -> Model registry (Exp→Stg→Cand→Prod) [Register]
- Model registry (Exp→Stg→Cand→Prod) -> Terraform plan/apply [Promote]
- ECR images (signed) -> Terraform plan/apply [Image]
- Prompt / schema / policy versions -> Shadow mode [Config]
- Shadow mode -> Canary by supplier segment [No unsafe diffs]
- Canary by supplier segment -> Production [Approved]
- Production -> Drift (PSI/KS) [Telemetry]
- Review & override rate --> Reviewer labels (Ground Truth) [Retrain loop (corrections → labels)]

**Components with no connection:** Optuna thresholds; Cost / page

## 6 Data Lineage & Privacy (6 · Data Lineage & Privacy Governance)

**① INGEST**

- Google Drive file (id, version) _(component)_
- SHA-256 content hash _(component)_
- Raw S3 (versioned, immutable) _(database)_

**② DETECT & PROTECT**

- Macie / PII scan _(component)_ `aws:macie`
- Mask bank/PII in logs & prompts _(component)_
- Tokenise bank details _(component)_

**③ EXTRACT & DERIVE**

- Extracted fields (+confidence, bbox) _(database)_
- Extraction run id + model/prompt ver _(database)_
- Comparison results & variances _(database)_

**④ DECIDE & RECORD**

- Policy / rule version _(database)_
- Outcome + anomaly codes _(database)_
- Evidence bundle (Object Lock) _(database)_

**⑤ GOVERN**

- Glue Data Catalog / lineage graph _(component)_ `aws:glue`
- OpenLineage events _(component)_
- Row-level security per legal entity _(component)_
- Per-entity KMS keys _(component)_ `aws:key_management_service`

**⑥ RETAIN & ACCESS**

- Retention + lifecycle tiers _(component)_
- Legal hold _(component)_
- Access logs (CloudTrail data events) _(component)_ `aws:cloudtrail`
- Redaction / deletion workflow _(component)_
- API: authorized consumers only _(component)_

**Connections**

- Google Drive file (id, version) -> SHA-256 content hash [Fingerprint]
- SHA-256 content hash -> Raw S3 (versioned, immutable) [Store]
- Raw S3 (versioned, immutable) -> Macie / PII scan [Scan]
- Macie / PII scan -> Mask bank/PII in logs & prompts [Findings]
- Mask bank/PII in logs & prompts -> Tokenise bank details [Redact]
- Raw S3 (versioned, immutable) -> Extracted fields (+confidence, bbox) [Extract]
- Extracted fields (+confidence, bbox) -> Extraction run id + model/prompt ver [Version]
- Extraction run id + model/prompt ver -> Comparison results & variances [Reconcile]
- Comparison results & variances -> Outcome + anomaly codes [Rules]
- Policy / rule version -> Outcome + anomaly codes [Policy]
- Outcome + anomaly codes -> Evidence bundle (Object Lock) [Bundle]
- Evidence bundle (Object Lock) -> Glue Data Catalog / lineage graph [Register]
- Glue Data Catalog / lineage graph -> OpenLineage events [Emit]
- Outcome + anomaly codes -> Row-level security per legal entity [Isolate]
- Evidence bundle (Object Lock) -> Retention + lifecycle tiers [Lifecycle]

**Components with no connection:** Per-entity KMS keys; Legal hold; Access logs (CloudTrail data events); Redaction / deletion workflow; API: authorized consumers only

## 7 Resilience & Fallback (7 · Resilience, HA & Multi-Provider Fallback)

**PRIMARY REGION (active)**

- API / Fargate (2 AZ) _(component)_ `aws:fargate`
- Step Functions _(component)_ `aws:step_functions`
- Aurora writer _(database)_
- S3 raw + evidence _(database)_
- SQS + DLQ _(component)_ `aws:sqs`
- Circuit breaker + backoff _(component)_

**DR REGION (warm standby)**

- API (scaled to min) _(component)_ `aws:fargate`
- Aurora Global replica _(database)_
- S3 CRR replica _(database)_
- Terraform-ready stack _(component)_

**EXTRACTION FALLBACK CHAIN**

- 1 · Textract AnalyzeExpense _(component)_ `aws:textract`
- 2 · Bedrock multimodal (model A) _(component)_ `aws:bedrock`
- 3 · Bedrock alt. model / region _(component)_ `aws:bedrock`
- 4 · Self-hosted LayoutLMv3 (SageMaker) _(component)_ `aws:sagemaker`
- 5 · Manual review queue (never guess) _(component)_
- Confidence gate per field _(decision)_

**RECOVERY PATTERNS**

- Route 53 health failover _(component)_ `aws:route_53`
- AWS Backup + PITR _(component)_ `aws:backup`
- DLQ + redrive _(component)_
- Idempotent replay _(component)_
- Game days / chaos tests _(component)_
- RTO 4h · RPO 15m (to be agreed) _(component)_

**Connections**

- API / Fargate (2 AZ) -> Step Functions [Start]
- Step Functions -> 1 · Textract AnalyzeExpense [Primary]
- 1 · Textract AnalyzeExpense -> Confidence gate per field [Fields]
- Confidence gate per field -> 2 · Bedrock multimodal (model A) [Low conf]
- 2 · Bedrock multimodal (model A) -> 3 · Bedrock alt. model / region [Throttle/err]
- 3 · Bedrock alt. model / region -> 4 · Self-hosted LayoutLMv3 (SageMaker) [Outage]
- 4 · Self-hosted LayoutLMv3 (SageMaker) -> 5 · Manual review queue (never guess) [Still unsure]
- SQS + DLQ -> DLQ + redrive [Max retries]
- Aurora writer -> Aurora Global replica [Replication]
- S3 raw + evidence -> S3 CRR replica [CRR]
- Circuit breaker + backoff -> 2 · Bedrock multimodal (model A) [Open → skip]

**Components with no connection:** API (scaled to min); Terraform-ready stack; Route 53 health failover; AWS Backup + PITR; Idempotent replay; Game days / chaos tests; RTO 4h · RPO 15m (to be agreed)

## 8 Workflow Orchestration (8 · Workflow Orchestration & Bounded AI Workers (no autonomous agents))

**SUPERVISOR (deterministic state machine)**

- Step Functions: per-document workflow _(component)_ `aws:step_functions`
- State store (DynamoDB) _(database)_
- Run context: policy/model versions _(component)_
- Human review task token _(component)_

**WORKERS (each single-purpose)**

- Classifier _(component)_
- Extractor (Textract) _(component)_
- Verifier (LLM, schema-bound) _(component)_
- Validator (math, dates, IDs) _(component)_
- PO resolver _(component)_
- Line matcher _(component)_
- Reconciler (rules) _(component)_
- Anomaly checker _(component)_
- Evidence writer _(component)_

**TOOL REGISTRY (allow-listed, read-only unless noted)**

- Drive API (read) _(component)_
- PO / ERP API (read) _(component)_
- Supplier master (read) _(component)_
- Results API (write, existing contract) _(component)_
- Aurora (write results) _(database)_
- S3 evidence (write-once) _(database)_

**DECISION GATES**

- Fields confident & valid? _(decision)_
- Exactly one eligible PO? _(decision)_
- All mandatory checks pass? _(decision)_
- Duplicate suspected? _(decision)_

**OUTCOMES (BRD §10)**

- Matched / within tolerance _(component)_
- Partially matched _(component)_
- Discrepancy detected _(component)_
- Duplicate suspected _(component)_
- Extraction failed / Requires review _(component)_
- Processing failed (retry) _(component)_

**Connections**

- Step Functions: per-document workflow -> Classifier [Invoke]
- Classifier -> Extractor (Textract)
- Extractor (Textract) -> Verifier (LLM, schema-bound) [Low conf only]
- Verifier (LLM, schema-bound) -> Validator (math, dates, IDs)
- Validator (math, dates, IDs) -> Fields confident & valid?
- Fields confident & valid? -> PO resolver [Yes]
- PO resolver -> Exactly one eligible PO?
- Exactly one eligible PO? -> Line matcher [Yes]
- Line matcher -> Reconciler (rules)
- Reconciler (rules) -> Anomaly checker
- Anomaly checker -> All mandatory checks pass?
- All mandatory checks pass? -> Matched / within tolerance [Yes]
- All mandatory checks pass? -> Duplicate suspected? [Check]
- Duplicate suspected? -> Duplicate suspected [Yes]
- Fields confident & valid? -> Extraction failed / Requires review [No]
- Exactly one eligible PO? -> Human review task token [Ambiguous]
- Evidence writer -> S3 evidence (write-once) [Write once]
- PO resolver -> PO / ERP API (read) [Read]
- Evidence writer -> Aurora (write results) [Persist]
- Step Functions: per-document workflow -> State store (DynamoDB) [State]

**Components with no connection:** Run context: policy/model versions; Drive API (read); Supplier master (read); Results API (write, existing contract); Partially matched; Discrepancy detected; Processing failed (retry)

**Diagram issues:**
- 7 edge(s) without a label

## 9 FinOps (9 · FinOps & Cost Optimization (LLM/Doc-AI spend control))

**TIERED EXTRACTION ROUTING**

- Doc-hash cache (skip re-extraction) _(database)_
- Textract first (cheapest per page) _(component)_ `aws:textract`
- Small LLM for low-conf fields _(component)_ `aws:bedrock`
- Larger LLM only for hard layouts _(component)_ `aws:bedrock`
- Prompt caching for schema/instructions _(component)_
- Batch inference for backlog _(component)_

**CACHING**

- Embedding cache (line descriptions) _(component)_ `aws:elasticache`
- Supplier / PO lookup cache _(database)_
- TTL + invalidation on PO change _(component)_
- Cache hit-rate metric _(component)_

**QUOTAS & BUDGETS**

- AWS Budgets per env _(component)_
- Per-entity page/token quotas _(component)_
- Cost Anomaly Detection _(component)_
- Hard LLM spend cap → fallback to review _(decision)_

**INFRA SAVINGS**

- Fargate Spot for batch workers _(component)_ `aws:fargate`
- S3 lifecycle (IA/Glacier) _(component)_ `aws:s3`
- VPC endpoints vs NAT data cost _(component)_
- Aurora Serverless v2 scaling _(component)_ `aws:aurora`

**COST VISIBILITY**

- Cost-allocation tags (entity, stage) _(component)_
- CUR → Athena _(component)_ `aws:athena`
- Cost per invoice KPI _(component)_
- Monthly FinOps review _(component)_

**Connections**

- Doc-hash cache (skip re-extraction) -> Textract first (cheapest per page) [Miss]
- Textract first (cheapest per page) -> Small LLM for low-conf fields [Low conf]
- Small LLM for low-conf fields -> Larger LLM only for hard layouts [Still low]
- Embedding cache (line descriptions) -> Cost per invoice KPI [Savings]
- Hard LLM spend cap → fallback to review -> Textract first (cheapest per page) [Breached]
- Cost-allocation tags (entity, stage) -> CUR → Athena [Allocate]
- CUR → Athena -> Cost per invoice KPI [Report]
- Per-entity page/token quotas -> Hard LLM spend cap → fallback to review [Limit]

**Components with no connection:** Prompt caching for schema/instructions; Batch inference for backlog; Supplier / PO lookup cache; TTL + invalidation on PO change; Cache hit-rate metric; AWS Budgets per env; Cost Anomaly Detection; Fargate Spot for batch workers; S3 lifecycle (IA/Glacier); VPC endpoints vs NAT data cost; Aurora Serverless v2 scaling; Monthly FinOps review

## 10 Governance & HITL (10 · AI Model Governance, Safety & HITL Evaluation)

**CONTINUOUS EVALUATION**

- Golden-set run _(database)_
- Field F1 / calibration _(component)_
- PO-ID accuracy _(component)_
- Unsafe approvals = 0 _(component)_

**GATES**

- Accuracy ≥ target? _(decision)_
- Zero unsafe approvals? _(decision)_
- Finance sign-off? _(decision)_

**REGISTRY STAGES**

- Experimental _(component)_
- Staging (shadow) _(component)_
- Candidate (canary) _(component)_
- Production _(component)_

**HUMAN-IN-THE-LOOP**

- Exception queue (SLA tracked) _(component)_
- Reviewer: approve/reject/correct _(component)_
- Reason codes captured _(component)_
- Feedback → golden set _(database)_

**POLICY GOVERNANCE**

- Tolerance & rounding policy _(database)_
- Controller approval + version _(component)_
- Authorised reprocess on rule change _(component)_
- Audit pack export _(component)_

**SAFETY CONTROLS**

- Kill-switch → review-only mode _(component)_
- PII / injection tests in CI _(component)_
- Model card + risk register _(component)_
- EU AI Act / ISO 42001 mapping _(component)_

**Connections**

- Golden-set run -> Field F1 / calibration [Score]
- Field F1 / calibration -> Accuracy ≥ target? [Pass?]
- Unsafe approvals = 0 -> Zero unsafe approvals?
- Accuracy ≥ target? -> Experimental [Yes]
- Zero unsafe approvals? -> Staging (shadow) [Yes]
- Finance sign-off? -> Candidate (canary) [Yes]
- Candidate (canary) -> Production [Promote]
- Exception queue (SLA tracked) -> Reviewer: approve/reject/correct [Assign]
- Reviewer: approve/reject/correct -> Reason codes captured
- Reason codes captured -> Feedback → golden set [Label]
- Feedback → golden set --> Golden-set run [Grow set]
- Controller approval + version -> Authorised reprocess on rule change [New version]
- Tolerance & rounding policy -> Controller approval + version [Draft]

**Components with no connection:** PO-ID accuracy; Audit pack export; Kill-switch → review-only mode; PII / injection tests in CI; Model card + risk register; EU AI Act / ISO 42001 mapping

**Diagram issues:**
- 2 edge(s) without a label
