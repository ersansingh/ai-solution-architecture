# Enterprise Multi-Cloud AI/ML Telemetry & Metrics Semantic Matrix

This reference matrix details the standard OpenTelemetry (OTel) metrics, logs, attributes, and span specifications across multi-cloud environments (AWS, Azure, GCP, On-Premises), foundation models, RAG, and compute hardware.

---

## 1. Multi-Cloud Resource & Provider Semantic Attributes

| Attribute Name | Allowed Values / Examples | Description |
| :--- | :--- | :--- |
| `cloud.provider` | `aws`, `azure`, `gcp`, `baremetal` | Designated cloud infrastructure provider. |
| `cloud.platform` | `aws_eks`, `azure_aks`, `gcp_gke`, `on_prem_k8s` | Underlying cloud container / compute orchestrator. |
| `cloud.region` | `us-east-1`, `eastus2`, `us-central1` | Geographic cloud region hosting the AI/ML workload. |
| `cloud.account.id` | AWS Account ID, Azure Subscription ID, GCP Project ID | Cloud tenant isolation account identifier. |
| `k8s.cluster.name` | `eks-prod-us-east-1`, `aks-prod-eastus`, `gke-prod-us-central1` | Kubernetes cluster name emitting telemetry. |

---

## 2. Multi-Provider LLM & Generative AI Semantic Conventions

| OTel Metric / Attribute Name | Instrument Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `gen_ai.system` | Attribute | String | LLM Provider (`aws.bedrock`, `azure.openai`, `gcp.vertex_ai`, `vllm`). |
| `gen_ai.request.model` | Attribute | String | Target model (`anthropic.claude-3-5-sonnet`, `gpt-4o`, `gemini-1.5-pro`, `llama-3-70b`). |
| `gen_ai.client.token.usage` | Counter / Histogram | `tokens` | Total tokens consumed by `type` (`input` vs `output`). |
| `gen_ai.client.operation.duration` | Histogram | `s` | E2E duration of the LLM generation request. |
| `gen_ai.client.time_to_first_token` | Histogram | `s` | Time elapsed from request start to first output token stream chunk (TTFT). |
| `gen_ai.client.time_per_output_token` | Histogram | `s` | Average generation latency per output token (TPOT). |
| `gen_ai.cost.estimated_usd` | Counter | `USD` | Calculated cost based on provider input/output token pricing rates. |

---

## 3. Multi-Cloud RAG & Vector Search Metrics

| Metric / Attribute Name | Instrument Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `db.system` | Attribute | String | Vector database provider (`opensearch`, `azure_ai_search`, `bigquery`, `qdrant`). |
| `rag.retriever.duration` | Histogram | `ms` | Time spent retrieving document chunks from target cloud vector store. |
| `rag.retriever.top_k` | Gauge / Attribute | Count | Number of nearest-neighbor chunks requested ($K$). |
| `rag.embedding.duration` | Histogram | `ms` | Time to generate dense vector embeddings via embedding API. |
| `rag.eval.faithfulness` | Gauge | Score [0,1]| RAGAS / TruLens faithfulness score (groundedness of output in context). |

---

## 4. Multi-Cloud GPU & Compute Infrastructure Metrics (NVIDIA DCGM)

| Metric Name | Instrument Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `DCGM_FI_DEV_GPU_UTIL` | Gauge | `%` | Percentage of time GPU kernel is actively executing. |
| `DCGM_FI_DEV_FB_USED` | Gauge | Bytes | Frame buffer / VRAM memory currently allocated. |
| `DCGM_FI_DEV_GPU_TEMP` | Gauge | °C | Current GPU core temperature. |
| `DCGM_FI_DEV_POWER_USAGE` | Gauge | Watts | Real-time power draw in Watts per GPU device. |
