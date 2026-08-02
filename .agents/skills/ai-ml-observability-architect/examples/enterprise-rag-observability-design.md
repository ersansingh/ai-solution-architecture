# Multi-Cloud Enterprise RAG Observability Architecture Example: Financial Knowledge Q&A Bot

> **Multi-Cloud Deployment Footprint**: 
> - **AWS**: AWS EKS (API Microservice) + AWS Bedrock (Claude 3.5 Sonnet) + OpenSearch Serverless
> - **Azure**: Azure AKS (Failover API) + Azure OpenAI Service (GPT-4o) + Azure AI Search
> - **GCP**: GCP GKE (Embedding & Batch Pipeline) + GCP Vertex AI (Gemini 1.5 Pro) + BigQuery Vector Search
> **Telemetry Stack**: ADOT / Azure OTel / GCP OTel Agents + Central OTel Gateway + Observe Inc. + Prometheus + Grafana Enterprise  

---

## 1. Executive Summary

This multi-cloud enterprise observability solution provides unified full-stack telemetry and operational monitoring for a high-throughput Financial Knowledge Q&A RAG application deployed across **AWS EKS**, **Azure AKS**, and **GCP GKE**. The system processes **5,000 queries per minute** across three cloud providers, dynamically routing between **AWS Bedrock (Claude 3.5 Sonnet)**, **Azure OpenAI (GPT-4o)**, and **GCP Vertex AI (Gemini 1.5 Pro)**.

The architecture features local Tier 1 OTel collectors emitting to a central **Multi-Cloud OpenTelemetry Collector Gateway** cluster. The Gateway enforces in-VPC PII scrubbing (SSNs, Credit Cards), attaches standard cloud resource attributes (`cloud.provider`, `cloud.region`, `k8s.cluster.name`), executes tail-based sampling (100% of errors/latencies > 2.5s, 5% of normal traffic), routes logs and traces to **Observe Inc.** for cross-cloud OPAL dataset analysis, and pushes high-cardinality time-series metrics to **Prometheus / Obstack** and **Grafana Enterprise**.

---

## 2. Multi-Cloud Telemetry Ingestion Topology

```
┌────────────────────────────────┐ ┌────────────────────────────────┐ ┌────────────────────────────────┐
│         AWS ENVIRONMENT        │ │       AZURE ENVIRONMENT        │ │        GCP ENVIRONMENT         │
│  [AWS EKS Pods / Bedrock]      │ │  [Azure AKS / Azure OpenAI]    │ │  [GCP GKE / Vertex AI]         │
│               │                │ │               │                │ │               │                │
│  [AWS ADOT DaemonSet Agent]    │ │  [Azure Monitor OTel Agent]    │ │  [GCP OTel Collector Agent]    │
└───────────────┬────────────────┘ └───────────────┬────────────────┘ └───────────────┬────────────────┘
                │ (OTLP / TLS)                     │ (OTLP / TLS)                     │ (OTLP / TLS)
                ▼                                  ▼                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            CENTRAL MULTI-CLOUD OPENTELEMETRY GATEWAY CLUSTER                         │
│  • Processors: `resourcedetection` (AWS, Azure, GCP), `memory_limiter`, `transform` (PII Scrubbing)  │
│  • Tail-Based Sampling: 100% Errors / Latencies > 2.5s, 5% Normal Traffic                            │
└───────────────┬──────────────────────────────────┬──────────────────────────────────┬────────────────┘
                │ (OTLP HTTP/gRPC)                 │ (Remote Write)                   │ (Cloud Native APIs)
                ▼                                  ▼                                  ▼
┌────────────────────────────────┐ ┌────────────────────────────────┐ ┌────────────────────────────────┐
│          OBSERVE INC.          │ │      OBSTACK / PROMETHEUS      │ │    CLOUD NATIVE AUDIT LOGS     │
│ Unified Logs & Traces,         │ │ Federated Prometheus TSDB,     │ │ AWS CloudWatch, Azure Monitor, │
│ Multi-Cloud OPAL Datasets,     │ │ PromQL Alert Rules             │ │ GCP Cloud Logging              │
│ Trace-to-Log Correlation       │ │                                │ │                                │
└────────────────────────────────┘ └────────────────────────────────┘ └────────────────────────────────┘
                                               │
                                               ▼
                                     [Grafana Enterprise]
                         (Multi-Cloud FinOps, Latency & GPU Dashboards)
```

---

## 3. Multi-Cloud OTel Gateway Configuration (`otel-collector-config.yaml`)

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
    limit_percentage: 75
    spike_limit_percentage: 15

  batch:
    send_batch_size: 8192
    timeout: 1s

  transform:
    error_mode: ignore
    log_statements:
      - context: log
        statements:
          - set(attributes["payload"], ReplaceAll(attributes["payload"], "\\b\\d{4}-\\d{4}-\\d{4}-\\d{4}\\b", "[REDACTED_CARD]"))

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
    endpoint: "http://prometheus-pushgateway.monitoring.svc.cluster.local:9090/api/v1/write"

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
      exporters: [otlp/observe]
```

---

## 4. Observe Inc. Multi-Cloud OPAL Queries

In Observe Inc., raw OTLP spans across AWS, Azure, and GCP are parsed into structured Datasets (`Multi_Cloud_RAG_Traces` and `Multi_Cloud_LLM_Spend`).

### Observe OPAL Query: Compare Latency & Spend across AWS Bedrock, Azure OpenAI, & GCP Vertex AI
```opal
dataset "Multi_Cloud_RAG_Traces"
| make_col total_cost_usd = (gen_ai_usage_input_tokens * 0.000003) + (gen_ai_usage_output_tokens * 0.000015)
| stats p95(duration_ms) as p95_ttft_ms,
        sum(total_cost_usd) as total_usd_spent
  by cloud_provider, gen_ai_system, gen_ai_request_model
```

---

## 5. Prometheus Multi-Cloud Alerting Rules (`alerts.yml`)

```yaml
groups:
  - name: multi_cloud_rag_alerts
    rules:
      - alert: LLMTimeToOneTokenExceeded
        expr: histogram_quantile(0.95, sum(rate(gen_ai_client_time_to_first_token_seconds_bucket[5m])) by (le, cloud_provider, gen_ai_system)) > 0.350
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "TTFT p95 exceeded 350ms on cloud {{ $labels.cloud_provider }} for model provider {{ $labels.gen_ai_system }}"

      - alert: GuardrailViolationSpike
        expr: sum(rate(ai_guardrail_blocked_total[5m])) by (cloud_provider) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Spike in prompt injection / guardrail blocks on cloud {{ $labels.cloud_provider }}"
```

---

## 6. Key Operational Metrics Summary across AWS, Azure, & GCP

* **Time To First Token (TTFT)**: p95 target < 250 ms (AWS Bedrock: 210 ms, Azure OpenAI: 230 ms, GCP Vertex AI: 240 ms).
* **Vector Retrieval Latency**: p95 target < 120 ms (OpenSearch: 85 ms, Azure AI Search: 95 ms, BigQuery Vector: 110 ms).
* **Multi-Cloud Token Spend**: Real-time USD spend tracking aggregated across AWS, Azure, and GCP.
* **In-VPC PII Redaction Rate**: 100% compliance prior to inter-cloud transmission and Observe Inc. export.
