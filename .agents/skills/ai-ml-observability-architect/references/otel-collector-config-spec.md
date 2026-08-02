# Multi-Cloud OpenTelemetry (OTel) Gateway Architecture & Configuration Specification

This reference document provides comprehensive guidance for deploying and configuring an OpenTelemetry Collector Gateway cluster across multi-cloud environments (AWS, Microsoft Azure, Google Cloud Platform, and On-Premises).

---

## 1. Multi-Cloud OpenTelemetry Collector Topology

```
┌────────────────────────────────┐ ┌────────────────────────────────┐ ┌────────────────────────────────┐
│         AWS ENVIRONMENT        │ │       AZURE ENVIRONMENT        │ │        GCP ENVIRONMENT         │
│  [AWS EKS Pods / ADOT Agent]   │ │  [Azure AKS / Azure OTel Agent]│ │  [GCP GKE / GCP OTel Agent]    │
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
```

---

## 2. Complete Multi-Cloud OTel Gateway Config (`otel-collector-config.yaml`)

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  prometheus:
    config:
      scrape_configs:
        - job_name: 'dcgm-gpu-exporter'
          scrape_interval: 5s
          static_configs:
            - targets: ['dcgm-exporter.monitoring.svc.cluster.local:9400']

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
    send_batch_max_size: 10240

  transform:
    error_mode: ignore
    log_statements:
      - context: log
        statements:
          - set(attributes["payload"], ReplaceAll(attributes["payload"], "\\b\\d{3}-\\d{2}-\\d{4}\\b", "[REDACTED_SSN]"))
          - set(attributes["payload"], ReplaceAll(attributes["payload"], "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b", "[REDACTED_EMAIL]"))
      - context: span
        statements:
          - set(attributes["gen_ai.prompt"], ReplaceAll(attributes["gen_ai.prompt"], "sk-[a-zA-Z0-9]{32,}", "[REDACTED_API_KEY]"))

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
      - name: sample_guardrail_blocks
        type: numeric_attribute
        numeric_attribute: {key: "ai.guardrail.blocked", value_condition: {equal_to: 1}}
      - name: probabilistic_sample
        type: probabilistic
        probabilistic: {sampling_percentage: 5.0}

exporters:
  otlp/observe:
    endpoint: "${OBSERVE_TENANT_ID}.collect.observeinc.com:443"
    headers:
      Authorization: "Bearer ${OBSERVE_BEARER_TOKEN}"

  prometheusremotewrite:
    endpoint: "http://prometheus-k8s.monitoring.svc.cluster.local:9090/api/v1/write"
    resource_to_telemetry_conversion:
      enabled: true

  awscloudwatchlogs:
    log_group_name: "/aws/eks/multi-cloud-observability/gateway"
    log_stream_name: "{PodName}"
    region: "${AWS_REGION}"

  azuremonitor:
    instrumentation_key: "${AZURE_INSTRUMENTATION_KEY}"

  googlecloudmonitoring:
    project: "${GCP_PROJECT_ID}"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [resourcedetection, memory_limiter, tail_sampling, transform, batch]
      exporters: [otlp/observe]
    metrics:
      receivers: [otlp, prometheus]
      processors: [resourcedetection, memory_limiter, batch]
      exporters: [prometheusremotewrite, otlp/observe, googlecloudmonitoring]
    logs:
      receivers: [otlp]
      processors: [resourcedetection, memory_limiter, transform, batch]
      exporters: [otlp/observe, awscloudwatchlogs, azuremonitor]
```
