# [Project Name]: Enterprise AI System Design Document

**Author**: [Architect Name]  
**Version**: 1.0  
**Status**: Draft / Under Review / Approved  
**Pattern**: [RAG / AI Agent / Fine-Tuned Model / Predictive ML / Multimodal / Streaming Voice]  
**Skill Compliance**: `ai-system-design-architect` (12-Step Enterprise Standard)

---

## 1. AI Problem Classification
- **Domain Category**: [Predictive AI / Generative AI / Knowledge Retrieval / Conversational AI / Document Intelligence / Decision Automation]
- **AI Archetype**: [Enterprise RAG / Autonomous Agent / Domain Fine-Tuned Model / Predictive ML / Multimodal OCR / Real-time Voice]
- **Problem Statement Summary**: Brief synthesis of the business challenge and AI capabilities required.

---

## 2. Architecture Pattern Selection & Rationale
- **Selected Pattern**: [e.g. Hybrid RAG + Agentic Tool Execution + Guardrails]
- **Pattern Comparison & Rationale**:
  - *Option A (Fine-Tuning)*: Evaluated but rejected due to high re-training cost and static knowledge cutoff.
  - *Option B (Pure LLM Prompting)*: Rejected due to hallucination risks and lack of domain document context.
  - *Selected Option (Hybrid RAG + Agents)*: Provides dynamic grounded retrieval, tool execution, and deterministic guardrails.

---

## 3. Architecture Reasoning
- **Compute Layer**: (e.g. AWS EKS / Azure AKS / GCP GKE with GPU node auto-scaling)
- **Model Engine**: (e.g. vLLM / TensorRT-LLM for self-hosted models or Azure OpenAI / Bedrock API)
- **Vector & Storage Layer**: (e.g. OpenSearch / Pinecone / pgvector with HNSW indexing)
- **Security & Guardrail Layer**: (e.g. NeMo Guardrails, Presidio PII Masking, KMS)

---

## 4. AI System Context & Boundary Table
| Context Attribute | Specification |
|---|---|
| **Target Users** | [e.g. 25,000 Enterprise Employees] |
| **Input Sources** | [e.g. PDFs, S3 Buckets, Confluence, SQL Databases] |
| **Output Interfaces** | [e.g. React Frontend, Slack Bot, REST API] |
| **Inference Type** | [e.g. Real-Time Streaming SSE (Server-Sent Events)] |
| **Target Cloud** | [AWS / Azure / GCP / Multi-Cloud] |
| **SLA & Latency Target** | [Availability 99.9%, TTFT < 800ms] |

---

## 5. Architecture Component Inventory (8 Enterprise Layers)
1. **User Layer**: Web Portal (React), Mobile App, Slack/Teams Integration.
2. **Application Layer**: CloudFront CDN, Application Load Balancers (ALB), Rate Limiters.
3. **API Layer**: API Gateway, OAuth2/OIDC Token Validation, GraphQL / REST Endpoints.
4. **AI / ML Layer**: Prompt Orchestration Engine, Agent Runtime, Embedding Service, LLM Serving Engine, Vector Search Engine.
5. **Data Layer**: Raw Data Lake (S3/GCS/Blob), Vector Database, Relational DB (PostgreSQL), Redis Cache.
6. **Security Layer**: WAF, IAM / SSO, KMS Encryption, PII Redaction, AI Guardrails, Audit Loggers.
7. **Infrastructure Layer**: VPC/VNet Subnets, Kubernetes Clusters (EKS/AKS/GKE), GPU Node Groups, PrivateLink.
8. **Operations & Observability Layer**: Prometheus, Grafana, OpenTelemetry Tracing, ELK/CloudWatch Logging, Model Drift & Hallucination Monitors.

---

## 6. Interaction Flow & Request Lifecycle
Step-by-step sequential sequence of events:
1. **User Request**: User sends query via Web App -> ALB -> API Gateway (Auth validation).
2. **Pre-Processing & Guardrails**: Query checked against PII Masking & Prompt Injection Guardrails.
3. **Semantic Cache & Retrieval**: Check Redis Semantic Cache. On cache miss, compute query vector embedding and query Vector DB (Top-K=5).
4. **LLM Synthesis & Streaming**: Prompt + Context sent to LLM Inference Engine. Output streamed back via SSE while logging metrics to OpenTelemetry.

---

## 7. The 10 Crucial Architecture Diagram Views

### 1. Logical Architecture View
Component interaction breakdown showing data processing and inference paths.
**Layout**: Layered columns (6+ color-coded containers), actors on edge, emoji service cards, header badges. 25+ components.

### 2. Infrastructure Architecture View
Topology diagram detailing Cloud Region, AZs, VPC/VNet, Public/Private Subnets, K8s Node Groups, and Storage.
**Layout**: Nested Cloud > Region > VPC > AZ > Subnet hierarchy with native cloud provider icons (AWS `mxgraph.aws4.resourceIcon`, Azure `img/lib/azure2/`, GCP `img/lib/google/`). Color-coded subnets (green=public, yellow=private, red=database).

### 3. Security Architecture View
Perimeter WAF, Auth flow, KMS encryption, Private subnets, mTLS, and AI Safety Guardrails.
**Layout**: 4-quadrant (IAM, Policy/Compliance, Monitoring/Audit, Threat Detection) with Governance Dashboard bar. Legend box.

### 4. Observability, Logging & Monitoring View
OpenTelemetry tracing, Prometheus metrics, ELK log aggregation, token usage, and hallucination tracking.
**Layout**: 4 horizontal rows (Collection, Visualization, Alerting, Operations), 4-6 components per row.

### 5. MLOps / LLMOps CI/CD Pipeline View
Source Control -> Automated Build -> Benchmark Evaluation -> Model Registry -> Canary K8s Deployment.
**Layout**: Left-to-right 6-stage pipeline with dashed feedback loop from Monitoring back to Source Control. Data Pipeline sub-section at bottom.

### 6. Data Lineage & Privacy Governance View
Presidio PII redaction, Row-Level Vector Tenant Isolation, and GDPR/EU AI Act data lineage tracking.
**Layout**: Top-to-bottom lineage flow with tenant isolation boundaries and audit trail sidebar.

### 7. Resilience, HA & Multi-Provider Fallback View
Multi-region failover, circuit breakers, and fallback routing (Primary LLM -> Secondary LLM -> Local SLM).
**Layout**: Multi-region diagram with active-active/passive failover paths and labeled fallback edges.

### 8. Multi-Agent Orchestration & Tool Execution View
Supervisor Agent -> Worker Agents (Search, Code, SQL) -> Execution Sandboxes -> Memory persistence.
**Layout**: Hierarchical agent tree with tool connections and memory store cylinders.

### 9. FinOps & Semantic Cache Cost Optimization View
Redis Semantic Cache, Model Cascading (routing simple queries to 8B SLM, complex queries to 70B+ LLM), and Token Budget Quotas.
**Layout**: Decision flow showing query routing paths with cost annotations on edges.

### 10. AI Model Governance, Safety & HITL Evaluation View
Automated Ragas/TruLens evaluation, Human-in-the-loop (HITL) review gates, and Model Registry staging gates.
**Layout**: Pipeline with decision diamond gates, HITL review queue, and Model Registry stage transitions (Experimental > Staging > Candidate > Production).

---

## 8. Draw.io Multi-Page XML File

Generate a complete, valid, importable `.drawio` XML file containing **all 10 architecture view pages**. The XML must meet these mandatory quality requirements:

- **10 pages** (one per architecture view listed in Section 7 above).
- **15+ meaningful components per page** -- never skeleton placeholders.
- **Native cloud provider icons** on Infrastructure pages (`mxgraph.aws4.resourceIcon` for AWS, `img/lib/azure2/` for Azure, `img/lib/google/` for GCP).
- **`shape=cylinder3`** for all databases and storage components.
- **`shadow=1`** on all inner service cards.
- **Container recipe**: outer rect + colored header badge + inner cards (see drawio_xml_spec.md Section 7).
- **Labeled edges**: all major connections have `edgeLabel` child cells with descriptive flow labels.
- **AWS group shapes** for Cloud/VPC/Subnet boundaries on Infrastructure pages (see drawio_xml_spec.md Section 3).
- **Container nesting** with `parent` attribute hierarchy (see drawio_xml_spec.md Section 4).
- **Emoji prefixes** in service card labels for visual scanning.

**Draw.io MCP workflow** (mandatory):
1. Use `search_shapes("aws <service>")` to get exact icon style strings before writing XML.
2. Write the `.drawio` file to disk.
3. Use `open_drawio_xml(content, routing="libavoid")` to preview and auto-route edges.
4. Use `get_page`/`set_page` to fix any page-level issues (overlaps, missing components).
5. Final validation: `open_drawio_xml(content, lightbox=true)` to confirm all 10 pages render.

Refer to:
- [Draw.io XML Specification](file:///.agents/skills/ai-system-design-architect/references/drawio_xml_spec.md) for XML syntax, icon catalogs, and shape patterns.
- [Visual Quality Standards](file:///.agents/skills/ai-system-design-architect/references/visual_quality_standards.md) for color palettes and per-view layout specs.

---

## 9. Infrastructure Architecture Specifications
- **VPC Network**: CIDR `10.0.0.0/16` across 3 Availability Zones.
- **Compute Cluster**: EKS / AKS / GKE cluster with auto-scaling GPU Node Pools.
- **Storage & Databases**: Encrypted Object Storage & Multi-AZ Vector Store.

---

## 10. Infrastructure as Code (Terraform)
Executable `main.tf` declaring VPC, Subnets, Kubernetes cluster, Vector DB, and IAM roles.

---

## 11. MLOps / LLMOps CI/CD Pipeline
Executable GitHub Actions / GitLab CI pipeline (`.github/workflows/mlops.yml`).

---

## 12. Operational & FinOps Model
- **SLA**: 99.9% Uptime.
- **Disaster Recovery**: Active-Passive Multi-Region failover (RPO < 15m, RTO < 1h).
- **FinOps Optimization**: Estimated monthly token & compute cost breakdown.
