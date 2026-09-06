# Cloud-Agnostic Enterprise AI Observability Architecture

**Platform**: Multi-Region Enterprise SaaS AI Platform  
**Telemetry Framework**: OpenTelemetry (OTel Gateway Dual-Tier Architecture)  
**Logs & Traces Backend**: Observe Inc. (OPAL Modeling & Distributed Trace Graphs)  
**Metrics & Alerting Backend**: Obstack (Prometheus TSDB, High-Cardinality Telemetry & Alertmanager)  
**Visualization Single Pane**: Grafana Enterprise & Observe Inc. Dashboards  
**Target Environments**: Multi-Cloud & Hybrid (AWS, Azure, GCP, On-Premises Bare-Metal GPU)  

---

## 1. Executive Summary & Observability Objectives

This architecture provides a **Cloud-Agnostic, Unified Full-Stack Telemetry Framework** for the Multi-Region SaaS AI Platform. By decoupling telemetry collection from cloud-proprietary logging services, the platform achieves vendor-neutral observability across 5 global regions, eliminating egress lock-in while consolidating four foundational observability tiers:

1. **Customer Journey Telemetry**: Tracking the user experience from login to intent execution, user satisfaction (CSAT), and funnel drop-offs.
2. **Business & FinOps Telemetry**: Measuring Daily Active Copilot Users (DACU), tenant consumption quotas, token burn rate vs. revenue margins, and tool ROI.
3. **Application & GenAI Telemetry**: Monitoring Time-to-First-Token (TTFT < 150ms P99 SLA), Time-per-Output-Token (TPOT), semantic prompt cache hit ratio (>40%), RAG context recall/precision, and model guardrail interventions.
4. **Infrastructure & GPU Telemetry**: Real-time NVIDIA DCGM GPU utilization, VRAM allocation, Karpenter node provisioning latency, and OTel collector buffer health.

---

## 2. Cloud-Agnostic Dual-Tier OTel Gateway Topology

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: PER-CLOUD / PER-NODE EDGE AGENTS (DaemonSets & Sidecars in EKS, AKS, GKE)      │
│  • AWS ADOT / Azure Monitor OTel / GCP OTel / OpenTelemetry Collector DaemonSets       │
│  • Local DCGM GPU Exporter, App W3C TraceContext, Kubelet cAdvisor                     │
│  • Local In-VPC PII Regex Masking & Resource Detection (`cloud.provider`, `tenant.id`) │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │ OTLP gRPC (mTLS Encrypted)
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 2: CENTRAL CLOUD-AGNOSTIC OTEL GATEWAY CLUSTER (Autoscaled HPA)                   │
│  • Memory Limiter (80% Hard Ceiling) & Batch Processor (8192 items / 200ms)            │
│  • Advanced PII Redaction & Transform Processor (Hash SSN, Credit Cards, PII)          │
│  • Tail-Based Sampler (100% of Errors & Spans > 2.5s; 5% Probabilistic Sample on OK)   │
└───────────────────────┬────────────────────────────────────────┬───────────────────────┘
                        │                                        │
           OTLP HTTP/gRPC (Logs & Spans)            Prometheus Remote Write (Metrics)
                        ▼                                        ▼
┌────────────────────────────────────────┐  ┌───────────────────────────────────────────┐
│ OBSERVE INC.                           │  │ OBSTACK / PROMETHEUS TSDB                 │
│  • Unified Multi-Cloud Log Lake        │  │  • High-Cardinality Metric Storage        │
│  • Trace-to-Log Span Graphs            │  │  • Pre-Aggregated Recording Rules         │
│  • OPAL Dataset Modeling (Cross-Cloud) │  │  • Real-Time Alertmanager & PagerDuty      │
└────────────────────────────────────────┘  └───────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SINGLE PANE OF GLASS: GRAFANA ENTERPRISE & OBSERVE INC. DASHBOARDS                     │
│  • Multi-Tenant Executive FinOps  • SRE GPU Health  • Real-time Customer Journey Funnel│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Four-Tier Telemetry Onboarding Matrix & Generation Mechanisms

This section details the exact instrumentation, mathematical formulations, and runtime mechanisms used to generate telemetry across all four dimensions.

---

### ① Customer Journey Telemetry

#### Telemetry Taxonomy & Metrics
| Metric / Span Attribute | Type | Description | Target SLO / Threshold |
|---|---|---|---|
| `customer.journey.stage` | Span Attribute | Tracks stages: `login`, `prompt_submit`, `intent_parse`, `rag_retrieval`, `llm_generate`, `tool_execute`, `user_feedback` | 100% trace coverage |
| `journey_funnel_completion_rate` | Gauge | Ratio of initiated copilot queries that complete successfully | > 98.5% |
| `copilot_user_csat_score` | Histogram | User thumbs up/down rating and explicit CSAT feedback | > 4.6 / 5.0 |
| `session_dropoff_latency_ms` | Histogram | Latency threshold at which users abandon in-flight queries | Alert if drop-off > 2% |
| `tool_action_accepted_ratio` | Gauge | Percentage of AI-generated code/workflows accepted without edit | > 85% |

#### How Customer Journey Metrics Are Generated:
1. **Frontend OTel Web SDK & W3C TraceContext Propagation**:
   - The React/Next.js client uses `@opentelemetry/sdk-trace-web` and `@opentelemetry/instrumentation-fetch`.
   - On each user action (e.g., submitting a prompt), an active root trace is created:
     ```typescript
     import { trace, context } from '@opentelemetry/api';

     const tracer = trace.getTracer('copilot-frontend');
     const span = tracer.startSpan('customer_copilot_journey', {
       attributes: {
         'customer.journey.stage': 'prompt_submit',
         'tenant.id': tenantId,
         'user.id': userId,
         'session.id': sessionId,
       },
     });
     // Propagate traceparent header via Server-Sent Events (SSE) HTTP POST
     ```
2. **Client-Side Latency & Drop-Off Detection**:
   - The frontend timer measures the duration from `prompt_submit` to receiving the first chunk (`first_token_received`).
   - If the user navigates away or closes the modal before the first token arrives, an `abort` event is caught, recording `session_dropoff_latency_ms` and marking the span as `status: ERROR, error.type: user_abandonment`.
3. **CSAT & Thumbs Up/Down Feedback Ingestion**:
   - When the user clicks 👍 / 👎, a lightweight telemetry event is sent to `/api/v1/telemetry/feedback`.
   - The API Gateway records `copilot_user_csat_score.record(score, { tenant_id, model_used, feature })` and attaches the user rating to the original `trace_id` in Observe Inc.

---

### ② Business & FinOps Metrics

#### Telemetry Taxonomy & Metrics
| Metric Name | Type | Description | Business Impact |
|---|---|---|---|
| `saas_dacu_count` | Gauge (Count) | Daily Active Copilot Users per tenant | User engagement & retention |
| `tenant_token_spend_usd` | Counter | Cumulative cost of LLM input/output tokens per tenant | Cost attribution & billing |
| `tenant_quota_utilization_ratio`| Gauge | Current token usage vs. contracted monthly quota tier | Upsell triggers & fair sharing |
| `semantic_cache_savings_usd` | Counter | Estimated cost saved by serving queries via Redis semantic cache | Direct gross margin impact |
| `tool_invocation_business_value`| Counter | Quantified hours saved per automated CRM/ERP tool execution | Enterprise ROI demonstration |

#### How Business & FinOps Metrics Are Generated:
1. **In-Flight Token Cost Calculation**:
   - Calculated inside the Agent API Gateway middleware after each stream finishes:
     $$\text{Cost}_{\text{USD}} = (N_{\text{input\_tokens}} \times \text{Rate}_{\text{input}}) + (N_{\text{output\_tokens}} \times \text{Rate}_{\text{output}})$$
   - In Python/FastAPI:
     ```python
     # Metric Generation in API Gateway / Router
     tenant_token_spend_counter.add(
         cost_usd,
         attributes={
             "tenant_id": tenant_id,
             "model": model_name,
             "subscription_tier": tenant_plan,
             "cloud_region": os.getenv("AWS_REGION")
         }
     )
     ```
2. **Semantic Cache Financial Savings**:
   - On a Redis Semantic Cache Hit (where cosine similarity $\ge 0.95$), the query is served in $<15\text{ms}$ with zero LLM invocation:
     $$\text{Savings}_{\text{USD}} = (\text{EstimatedTokens} \times \text{Rate}_{\text{frontier\_llm}})$$
   - Emits `semantic_cache_savings_usd.add(savings, {"tenant_id": tenant_id})`.
3. **Daily Active Copilot Users (DACU) Aggregation**:
   - Obstack / Prometheus evaluates a hyperloglog recording rule from unique `user.id` tags in traces every 5 minutes:
     ```yaml
     - record: tenant:saas_dacu_count
       expr: count by (tenant_id) (count_over_time(copilot_requests_total[24h]))
     ```

---

### ③ Application & GenAI Metrics

#### Telemetry Taxonomy & Metrics
| Metric Name | Type | Description | Target SLA / SLO |
|---|---|---|---|
| `gen_ai.client.ttft` | Histogram | Time to First Token (TTFT) across 5 global regions | **< 150 ms (P99)** |
| `gen_ai.client.tpot` | Histogram | Time per Output Token (streaming throughput) | **< 20 ms / token** |
| `semantic_cache_hit_ratio` | Gauge | Proportion of requests resolved by Redis Semantic Cache | **> 40% hit rate** |
| `rag.evaluation.faithfulness` | Gauge | Ragas grounding score (factual consistency with context) | **≥ 0.88** |
| `rag.evaluation.context_recall`| Gauge | Proportion of necessary reference chunks retrieved | **≥ 0.90** |
| `guardrails_intervention_count`| Counter | Number of prompts/outputs blocked by NeMo or Presidio | Real-time security alert |
| `model_fallback_triggered_total`| Counter | Number of circuit breaker escalations (Local vLLM -> Bedrock) | Track regional degradation |

#### How Application & GenAI Metrics Are Generated:
1. **High-Precision TTFT and TPOT Streaming Timer**:
   - Generated inside the vLLM / Bedrock streaming response generator using Python's `time.perf_counter()`:
     ```python
     start_time = time.perf_counter()
     first_token_received = False
     token_timestamps = []

     async for chunk in model_stream:
         now = time.perf_counter()
         if not first_token_received:
             ttft = (now - start_time) * 1000  # ms
             ttft_histogram.record(ttft, {"tenant_id": tenant_id, "model": model_id, "region": region})
             first_token_received = True
         token_timestamps.append(now)

     # Calculate Time Per Output Token (TPOT)
     if len(token_timestamps) > 1:
         total_gen_time = token_timestamps[-1] - token_timestamps[0]
         tpot = (total_gen_time / (len(token_timestamps) - 1)) * 1000  # ms/token
         tpot_histogram.record(tpot, {"tenant_id": tenant_id, "model": model_id})
     ```
2. **Automated Ragas & TruLens Quality Scoring**:
   - An asynchronous worker samples 5% of completed RAG queries from Observe Inc. and evaluates Faithfulness and Answer Relevance against retrieved vector chunks:
     ```python
     score = evaluate_faithfulness(question=query, contexts=retrieved_chunks, answer=response)
     rag_faithfulness_gauge.set(score, {"tenant_id": tenant_id, "index": "knowledge_base_v2"})
     ```
3. **Guardrail & Security Interceptor Hooks**:
   - NeMo and Presidio wrappers intercept prompts and outputs. If an injection attempt or unredacted PII is caught, they trigger:
     ```python
     guardrail_counter.add(1, {"violation_type": "prompt_injection", "tenant_id": tenant_id, "rule": "jailbreak_v3"})
     ```

---

### ④ Infrastructure & Fleet Metrics

#### Telemetry Taxonomy & Metrics
| Metric Name | Type | Description | Target Threshold |
|---|---|---|---|
| `container_gpu_utilization` | Gauge (DCGM) | NVIDIA L4 / Trainium Streaming Multiprocessor (SM) util | 75% – 90% optimal |
| `container_gpu_memory_used_bytes`| Gauge (DCGM) | VRAM allocation per model instance | Alert if VRAM > 92% |
| `karpenter_node_provision_duration_seconds`| Histogram | Latency to provision and join new GPU nodes | **< 60 seconds** |
| `spot_interruption_warning_total`| Counter | AWS 2-minute spot termination notices handled | 100% graceful drain |
| `otelcol_exporter_queue_dropped_metric_points`| Counter | Telemetry dropped due to network or downstream backpressure | **0 drops** |

#### How Infrastructure & Fleet Metrics Are Generated:
1. **NVIDIA DCGM Exporter DaemonSet**:
   - Runs as a Kubernetes DaemonSet on all GPU nodes (`g6.2xlarge`, `trn1`), directly querying the NVIDIA NVML hardware kernel driver:
   - Scraped every 10 seconds via Prometheus endpoint `http://<node-ip>:9400/metrics` by the Tier 1 OTel Collector.
2. **Karpenter Autoscaler Instrumentation**:
   - The Karpenter controller exposes native metrics on port `:8080/metrics`:
   - Emits `karpenter_node_provision_duration_seconds` upon binding an EC2 instance to the EKS cluster.
3. **Spot Termination Warning Webhook**:
   - AWS Node Termination Handler listens for AWS EventBridge 2-minute rebalance/spot termination warnings on the instance metadata service (`http://169.254.169.254/latest/meta-data/events/recommendations/rebalance`).
   - Immediately emits `spot_interruption_warning_total.add(1, {"instance_id": id, "region": region})` and triggers pod evacuation to warm pools.

---

## 4. Observe Inc. Integration & OPAL Dataset Modeling

Observe Inc. is the unified multi-cloud destination for logs, traces, and structural event modeling.

### Key Capabilities in Observe Inc.:
1. **Unified Multi-Cloud Schema**: Ingests OTLP logs and traces tagged with `cloud.provider`, `tenant_id`, `service.name`, and `gen_ai.*` attributes.
2. **Trace-to-Log Correlation**: Automatic bi-directional navigation from high-latency LLM spans directly into deep container and guardrail logs.
3. **OPAL (Observe Processing & Analysis Language) Queries**:
   ```opal
   // OPAL Pipeline: Identify High-Latency Multi-Region Tenants with Guardrail Triggers
   make_col
     tenant_id:string(fields.tenant_id),
     region:string(fields.cloud_region),
     ttft_ms:float64(fields.gen_ai_client_ttft_ms),
     guardrail_blocked:bool(fields.guardrail_blocked)
   | filter ttft_ms > 150.0 or guardrail_blocked == true
   | stats
     p99_ttft = quantile(ttft_ms, 0.99),
     total_violations = count_if(guardrail_blocked),
     total_requests = count()
     by tenant_id, region
   ```

---

## 5. Obstack & Prometheus Metrics Configuration

Obstack stores high-cardinality time-series metrics scraped via OTel Collector's Prometheus Remote-Write Exporter.

### Sample Prometheus Alerting Rules (`alerts.yml`):
```yaml
groups:
  - name: saas_ai_platform_slo_alerts
    rules:
      - alert: CopilotTTFTBreachP99
        expr: histogram_quantile(0.99, sum(rate(gen_ai_client_ttft_bucket[5m])) by (le, region, tenant_id)) > 0.150
        for: 2m
        labels:
          severity: critical
          tier: ai-inference
        annotations:
          summary: "P99 Time to First Token exceeded 150ms SLA in {{ $labels.region }} for tenant {{ $labels.tenant_id }}"
          description: "Current P99 TTFT is {{ $value }}s, breaching the sub-150ms contract."

      - alert: SemanticCacheHitRatioLow
        expr: sum(rate(semantic_cache_hits_total[10m])) / sum(rate(semantic_cache_requests_total[10m])) < 0.25
        for: 15m
        labels:
          severity: warning
          tier: finops
        annotations:
          summary: "Semantic Prompt Cache hit ratio dropped below 25%"
          description: "Cache efficiency is currently at {{ $value | humanizePercentage }}. GPU costs will increase."

      - alert: GPUVRAMExhaustionImminent
        expr: container_gpu_memory_used_bytes / container_gpu_memory_total_bytes > 0.92
        for: 1m
        labels:
          severity: critical
          tier: infrastructure
        annotations:
          summary: "GPU VRAM utilization above 92% on {{ $labels.node }}"
          description: "Model replica on {{ $labels.pod }} risks OOM crash."
```

---

## 6. Production OpenTelemetry Collector Configuration (`otel-collector-config.yaml`)

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
        - job_name: 'dcgm-gpu-metrics'
          scrape_interval: 10s
          static_configs:
            - targets: ['localhost:9400']

processors:
  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
    spike_limit_percentage: 20

  resourcedetection:
    detectors: [env, system, eks, gcp, azure]
    timeout: 2s
    override: false

  transform/pii_scrubbing:
    error_mode: ignore
    log_statements:
      - context: log
        statements:
          - replace_pattern(body, "(?i)\\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}\\b", "[EMAIL_REDACTED]")
          - replace_pattern(body, "\\b(?:\\d[ -]*?){13,16}\\b", "[CARD_REDACTED]")

  tail_sampling:
    decision_wait: 10s
    num_traces: 10000
    expected_new_traces_per_sec: 2000
    policies:
      [
        {
          name: errors-policy,
          type: status_code,
          status_code: { status_codes: [ERROR] }
        },
        {
          name: high-latency-policy,
          type: numeric_attribute,
          numeric_attribute: { key: "gen_ai.client.ttft", value_condition: { greater_than_or_equal: 150 } }
        },
        {
          name: probabilistic-sample,
          type: probabilistic,
          probabilistic: { sampling_percentage: 5.0 }
        }
      ]

  batch:
    send_batch_size: 8192
    timeout: 200ms

exporters:
  # Observe Inc. Exporter for Unified Logs and Distributed Traces
  otlphttp/observe:
    endpoint: "https://${OBSERVE_CUSTOMER_ID}.collect.observeinc.com/v1/otel"
    headers:
      Authorization: "Bearer ${OBSERVE_COLLECTOR_TOKEN}"

  # Obstack / Prometheus Remote-Write Exporter for High-Cardinality Metrics
  prometheusremotewrite/obstack:
    endpoint: "https://obstack-metrics.internal.saas-ai.net/api/v1/write"
    headers:
      X-Scope-OrgID: "enterprise-saas"

  # Cloud-Native Fallback Exporter (AWS CloudWatch / Audit Compliance)
  awscloudwatchlogs:
    log_group_name: "/saas-ai-platform/audit-logs"
    region: "us-east-1"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, tail_sampling, batch]
      exporters: [otlphttp/observe]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, transform/pii_scrubbing, batch]
      exporters: [otlphttp/observe, awscloudwatchlogs]
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [prometheusremotewrite/obstack]
```

---
