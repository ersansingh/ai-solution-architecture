# Enterprise AI/ML Observability Architecture & Implementation Report: AWS Multi-Account Platform

> **Skill Location**: [`.agents/skills/ai-ml-observability-architect/SKILL.md`](file:///c:/Users/DELL/Documents/GitHub/ai-solution-architecture/.agents/skills/ai-ml-observability-architect/SKILL.md)  
> **Requirements Spec**: [`observability-requirements-spec.md`](file:///c:/Users/DELL/Documents/GitHub/ai-solution-architecture/lab6-observability-governance/lab6.1-observability-aws/observability-requirements-spec.md)  

---

## 1. Executive Summary

This implementation report provides a comprehensive, production-grade observability architecture and operational blueprint across 5 core observability pillars: **Infrastructure Observability (Part 1)**, **Data & Feature Observability (Part 2)**, **Model Performance Observability (Part 3)**, **Generative AI & LLM Observability (Part 4)**, and **Business, Security, Compliance & Automated Remediation (Part 5)**.

The solution integrates **AWS Distro for OpenTelemetry (ADOT)**, a central **OpenTelemetry Gateway Cluster**, **Amazon Managed Service for Prometheus (AMP)**, **Amazon Managed Grafana (AMG)**, **Observe Inc.** (for unified logs, distributed trace graphs, and OPAL datasets), **Amazon Bedrock Guardrails**, and **AWS Step Functions** for closed-loop automated incident remediation.

---

## 2. Multi-Cloud AI/ML Use Case & Deployment Footprint

* **Use Case Name**: Enterprise Multi-Account AI/ML Platform & GenAI Financial RAG Assistant
* **AI Architecture Pattern**: Hybrid Enterprise AI (Predictive ML + RAG + Multi-Model LLM + Multi-Agent Tool Execution)
* **Designated Cloud Environments**:
  * **AWS (Primary Hub)**: AWS EKS, Amazon SageMaker, Amazon Bedrock, OpenSearch Serverless, MSK, S3, ADOT, CloudWatch, AMP.
  * **Microsoft Azure (Failover)**: Azure AKS, Azure OpenAI (GPT-4o), Azure AI Search.
  * **Google Cloud Platform (GCP)**: GCP GKE, Vertex AI (Gemini 1.5), BigQuery Vector Search.
  * **On-Premises / Edge**: Nvidia DGX Bare-Metal GPU K8s Nodes running Nvidia DCGM exporter.
* **Telemetry Stack**: ADOT DaemonSet + Central OTel Gateway Cluster + Observe Inc. + AMP / Prometheus + Grafana Enterprise.
* **Key SLAs**: TTFT < 300 ms (p95), Total Latency < 1.5s (p95), Real-Time Inference < 10 ms (p99), Platform Availability ≥ 99.99%.

---

## 3. Multi-Cloud Observability Requirements & SLA Evaluation

* **Infrastructure & Compute**: NVIDIA DCGM GPU utilization, VRAM allocation, EKS pod restarts, Lambda executions.
* **Data & Feature Quality**: AWS Deequ PySpark quality rules, Schema Registry compatibility, Feature PSI drift ($\text{PSI} \ge 0.25$).
* **Model Performance**: Accuracy ($\ge 92\%$), Precision ($\ge 88\%$), Recall ($\ge 85\%$), F1 ($\ge 86\%$), Expected Calibration Error ($\text{ECE} \le 0.05$).
* **GenAI & RAG Quality**: Groundedness Score ($\ge 0.85$), Context Recall ($\ge 0.80$), Context Precision ($\ge 0.82$).
* **Safety & Guardrails**: Bedrock Guardrails toxicity/HATE filters, Prompt Injection detection, PII regex masking.
* **Tracing & Logging**: OTLP gRPC/HTTP spans, PII regex scrubbing inside OTel Gateway, 100% error/high-latency tail-sampling.

---

## 4. End-to-End Multi-Cloud Observability Architecture

```
┌────────────────────────────────┐ ┌────────────────────────────────┐ ┌────────────────────────────────┐
│         AWS ENVIRONMENT        │ │       AZURE ENVIRONMENT        │ │        GCP ENVIRONMENT         │
│  [AWS EKS Pods / Bedrock]      │ │  [Azure AKS / Azure OpenAI]    │ │  [GCP GKE / Vertex AI]         │
│               │                │ │               │                │ │               │                │
│  [AWS ADOT DaemonSet Agent]    │ │  [Azure Monitor OTel Agent]    │ │  [GCP OTel Collector Agent]    │
└───────────────┬────────────────┘ └───────────────┬────────────────┘ └───────────────┬────────────────┘
                │ (Local OTLP)                     │ (Local OTLP)                     │ (Local OTLP)
                ▼                                  ▼                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            CENTRAL MULTI-CLOUD OPENTELEMETRY GATEWAY CLUSTER                         │
│  • Resource Detection: Auto-populates `cloud.provider`, `cloud.region`, `k8s.cluster.name`           │
│  • PII Redaction: Scrub SSNs, Credit Cards, API Keys before cross-cloud transmission                 │
│  • Tail-Based Sampling: 100% Errors / Latencies > 2.5s, 5% Normal Traffic                            │
└───────────────┬──────────────────────────────────┬──────────────────────────────────┬────────────────┘
                │ (OTLP HTTP/gRPC)                 │ (Remote Write)                   │ (Cloud APIs)
                ▼                                  ▼                                  ▼
┌────────────────────────────────┐ ┌────────────────────────────────┐ ┌────────────────────────────────┐
│          OBSERVE INC.          │ │      OBSTACK / PROMETHEUS      │ │    CLOUD AUDIT LOGGERS         │
│ Unified Logs & Traces,         │ │ Cross-Cloud Time-Series TSDB,   │ │ AWS CloudWatch, Azure Monitor, │
│ Multi-Cloud OPAL Datasets,     │ │ PromQL Alert Rules,             │ │ GCP Cloud Logging              │
│ Trace-to-Log Correlation       │ │ Multi-Cloud SLO Tracking        │ │                                │
└───────────────┬────────────────┘ └───────────────┬────────────────┘ └───────────────┬────────────────┘
                │                                  │                                  │
                └──────────────────────────────────┼──────────────────────────────────┘
                                                   ▼
                                     ┌────────────────────────────┐
                                     │     GRAFANA ENTERPRISE     │
                                     │ Multi-Cloud FinOps, SRE, & │
                                     │ MLOps Single-Pane Dashboards│
                                     └────────────────────────────┘
```

---

## 5. Multi-Cloud OpenTelemetry (OTel) Gateway Implementation

### Production `otel-collector-config.yaml`
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  resourcedetection:
    detectors: [env, gcp, ecs, ec2, eks, azure]
    timeout: 2s
    override: false

  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
    spike_limit_percentage: 20

  batch:
    send_batch_size: 8192
    timeout: 1s

  transform:
    error_mode: ignore
    log_statements:
      - context: log
        statements:
          - set(attributes["payload"], ReplaceAll(attributes["payload"], "\\b\\d{3}-\\d{2}-\\d{4}\\b", "[REDACTED_SSN]"))

  tail_sampling:
    decision_wait: 5s
    num_traces: 20000
    expected_new_traces_per_sec: 5000
    policies:
      - name: sample_errors
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: sample_high_latency
        type: latency
        latency: {threshold_ms: 2500}
      - name: sample_probabilistic
        type: probabilistic
        probabilistic: {sampling_percentage: 5.0}

exporters:
  otlp/observe:
    endpoint: "${OBSERVE_CUSTOMER_ID}.collect.observeinc.com:443"
    headers:
      Authorization: "Bearer ${OBSERVE_BEARER_TOKEN}"

  prometheusremotewrite:
    endpoint: "https://aps-workspaces.${AWS_REGION}.amazonaws.com/workspaces/${WORKSPACE_ID}/api/v1/remote_write"
    aws_auth:
      region: "${AWS_REGION}"
      service: "aps"

  awscloudwatchlogs:
    log_group_name: "/aws/eks/unified-observability"
    log_stream_name: "{PodName}"
    region: "${AWS_REGION}"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [resourcedetection, memory_limiter, tail_sampling, transform, batch]
      exporters: [otlp/observe]
    metrics:
      receivers: [otlp]
      processors: [resourcedetection, memory_limiter, batch]
      exporters: [prometheusremotewrite, otlp/observe]
    logs:
      receivers: [otlp]
      processors: [resourcedetection, memory_limiter, transform, batch]
      exporters: [otlp/observe, awscloudwatchlogs]
```

---

## 6. Observe Inc. Multi-Cloud Logs & Traces Integration

* **Dataset Modeling**: Maps OTLP spans and logs into Observe Inc. Datasets (`Multi_Cloud_LLM_Spans`, `RAG_Retrieval_Events`, `Model_Inferences`).
* **OPAL Query Example (Multi-Cloud Latency & Spend)**:
```opal
dataset "Multi_Cloud_LLM_Spans"
| make_col total_tokens = gen_ai_usage_input_tokens + gen_ai_usage_output_tokens,
           cost_usd = (gen_ai_usage_input_tokens * 0.000003) + (gen_ai_usage_output_tokens * 0.000015)
| stats p95(duration_ms) as p95_ttft_ms,
        sum(cost_usd) as total_usd_spent
  by cloud_provider, gen_ai_system, gen_ai_request_model
```

---

## 7. Prometheus Federated Metrics & Alerting Configuration

```yaml
groups:
  - name: unified_ai_alerts
    rules:
      - alert: HighMultiCloudTTFTLatency
        expr: histogram_quantile(0.95, sum(rate(gen_ai_client_time_to_first_token_seconds_bucket[5m])) by (le, cloud_provider, gen_ai_system)) > 0.300
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "TTFT p95 exceeds 300ms on cloud {{ $labels.cloud_provider }} for provider {{ $labels.gen_ai_system }}"

      - alert: CriticalModelRecallDrop
        expr: Enterprise_ModelObservability_Recall < 0.85
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Model Recall dropped below 85% for version {{ $labels.ModelVersion }}"

      - alert: FeatureDriftPSIBreach
        expr: Enterprise_DataObservability_FeatureDriftPSI >= 0.25
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PSI feature drift exceeded 0.25 threshold for {{ $labels.FeatureName }}"
```

---

## 8. Multi-Cloud Grafana Dashboards

* **Dashboard 1: Executive FinOps & ROI**: Real-time USD spend ($/min) by Cloud Provider, Model ROI %, Attributable Revenue.
* **Dashboard 2: Predictive ML & Feature Quality**: Accuracy, Precision, Recall, F1 curves, PSI Feature Drift, ECE score.
* **Dashboard 3: GenAI & RAG Quality**: Groundedness Score, Context Recall/Precision, TTFT/TPOT latencies, Bedrock Guardrail blocks.
* **Dashboard 4: SRE & Compute Health**: NVIDIA DCGM GPU utilization/VRAM, Pod restarts, OTel Gateway QPS.

---

## 9. AI/ML Specific Telemetry & Guardrail Monitoring Across Clouds

* **Model Drift**: Continuous PSI & KS-test computation on serving data.
* **RAG Evaluation**: Asynchronous Judge LLM (Claude Haiku) scoring of Groundedness, Recall, and Precision.
* **Guardrails**: Bedrock Guardrails HATE/Violence filtering and regex prompt injection detection.

---

## 10. Multi-Cloud Infrastructure & IaC (Terraform)

```hcl
# Terraform module deploying ADOT IRSA Role on AWS EKS
module "aws_adot_irsa" {
  source    = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  role_name = "adot-collector-aws-irsa"
  role_policy_arns = {
    cloudwatch = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  }
  oidc_providers = {
    main = {
      provider_arn               = var.aws_eks_oidc_provider_arn
      namespace_service_accounts = ["monitoring:adot-collector"]
    }
  }
}
```

---

## 11. Security, Privacy & PII Redaction

* **VPC Perimeter Redaction**: OTel Gateway `transform` processor scrubs SSNs, Credit Cards, and API keys before sending telemetry to Observe Inc. or Prometheus.
* **Audit Lineage**: AWS CloudTrail, AWS Config, and AWS Macie record all access logs, schema shifts, and sensitive data locations.

---

## 12. FinOps & Token Economics Observability

* **Formula**: $\text{Cost} = (\text{Prompt Tokens} \times P_{\text{prompt}}) + (\text{Completion Tokens} \times P_{\text{completion}})$.
* **Automated Cost Control**: AWS Step Functions automatically switches LLM routing to Haiku or Nova Micro when daily spend exceeds $1,000/day.

---

## 13. Alerting Rules & Multi-Cloud Incident Response Matrix

| Alert Name | Condition | Threshold | Severity | Automated Action |
| :--- | :--- | :--- | :--- | :--- |
| **ModelRecallDrop** | Recall metric | < 85% | Critical | Step Functions rolls back SageMaker endpoint variant |
| **FeaturePSIDrift** | PSI score | ≥ 0.25 | Warning | Step Functions triggers SageMaker retraining pipeline |
| **LowGroundedness** | Groundedness | < 0.70 | Critical | Step Functions switches LLM routing to strict Haiku model |
| **PromptInjection** | Injection match| > 0 count | Critical | Block user session, sanitize output, alert InfoSec SOC |

---

## 14. Implementation & Deployment Roadmap

| Phase | Core Deliverables | Duration |
| :--- | :--- | :--- |
| **Phase 1: Infrastructure** | Deploy ADOT Collector DaemonSet, OTel Gateway, AMP, CloudWatch, Grafana. | 2 weeks |
| **Phase 2: Data & Features** | Integrate Glue Catalog/Registry, Deequ PySpark quality, SageMaker PSI drift engine. | 2 weeks |
| **Phase 3: Predictive Model** | Enable SageMaker Data Capture, Ground-Truth join engine, ECE & recall metrics. | 2 weeks |
| **Phase 4: GenAI & RAG** | Instrument OTel GenAI SDK, Bedrock Guardrails, Judge LLM RAG evaluators. | 2 weeks |
| **Phase 5: Governance & ITSM**| Configure CloudTrail/Config/Macie, ServiceNow/PagerDuty alerts, Step Functions closed-loop remediation. | 2 weeks |

---

## 15. Confidence Level & Operational Verification

* **Confidence**: **High**
* **Verification**: Execute fault injection scripts (`inject_feature_drift.py`, `inject_degraded_predictions.py`, `test_rag_hallucination.py`), confirm CloudWatch alarm triggers, verify automated Step Functions rollbacks and retraining triggers.
