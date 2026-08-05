# Enterprise RAG System Architecture & Design Document

**Author**: Chief Enterprise AI Architect  
**Version**: 1.0  
**Status**: Approved  
**Pattern**: Hybrid RAG + Vector DB + NeMo Guardrails + Semantic Cache  
**Skill Compliance**: `ai-system-design-architect` (12-Step Enterprise Standard)

---

## 1. AI Problem Classification
- **Domain Category**: Knowledge Retrieval & Generative AI.
- **AI Archetype**: Enterprise RAG Assistant over 500,000+ internal documents (PDFs, DOCX, Confluence, SharePoint, SQL DBs).
- **Problem Statement Summary**: Provide 25,000 enterprise employees with a secure, sub-second conversational search assistant that returns answers strictly grounded in enterprise documents with exact source citations while preventing PII leakage and prompt injection.

---

## 2. Architecture Pattern Selection & Rationale
- **Selected Pattern**: Hybrid Dense-Sparse RAG + NeMo Guardrails + Redis Semantic Cache.
- **Pattern Comparison & Rationale**:
  - *Fine-Tuning*: Rejected due to high retraining overhead and inability to enforce document-level Row-Level Security (RLS).
  - *Basic RAG*: Rejected due to vector-only retrieval precision drops on domain terminology.
  - *Hybrid RAG + Guardrails (Selected)*: Combines dense vector embeddings (Text-Embedding-004) + sparse keyword search (BM25 in OpenSearch) with NeMo Guardrails for safety and Redis for semantic prompt caching.

---

## 3. Architecture Reasoning
- **Compute Layer**: AWS EKS (Elastic Kubernetes Service) with g5.2xlarge GPU node groups for vLLM local model serving and CPU node pools for microservices.
- **Vector & Storage Layer**: Amazon OpenSearch Service (HNSW vector index) + Amazon S3 with KMS Customer Managed Keys.
- **Security & Guardrail Layer**: Presidio PII Masking Engine + NeMo Guardrails (Input & Output validation).

---

## 4. AI System Context & Boundary Table
| Context Attribute | Specification |
|---|---|
| **Target Users** | 25,000 Enterprise Employees (Peak 200 RPS) |
| **Input Sources** | S3 Document Lake, SharePoint, Confluence, PostgreSQL |
| **Output Interfaces** | React Web Portal, Slack Bot, REST API |
| **Inference Type** | Real-Time SSE (Server-Sent Events) Streaming |
| **Target Cloud** | AWS (us-east-1, Multi-AZ) |
| **SLA & Latency Target** | 99.9% Uptime, Time-To-First-Token (TTFT) < 800ms |

---

## 5. Architecture Component Inventory (8 Enterprise Layers)
1. **User Layer**: Web Portal (React), Mobile Client, Slack Bot.
2. **Application Layer**: CloudFront CDN, AWS Application Load Balancer (ALB).
3. **API Layer**: AWS API Gateway, Cognito OAuth2/OIDC Auth Server.
4. **AI / ML Layer**: LangGraph Agent Orchestrator, vLLM Model Engine, Embedding Service, OpenSearch Vector Store.
5. **Data Layer**: S3 Document Lakehouse, PostgreSQL Metadata DB, Redis Semantic Cache.
6. **Security Layer**: AWS WAF, KMS Encryption, Presidio PII Redaction, NeMo Guardrails, IAM Roles.
7. **Infrastructure Layer**: AWS VPC (3 AZs), EKS Cluster, PrivateLink, NAT Gateways.
8. **Operations & Observability Layer**: Prometheus, Grafana, OpenTelemetry Tracing, CloudWatch Logs, Ragas Evaluation Engine.

---

## 6. Interaction Flow & Request Lifecycle
1. **User Prompt**: Employee submits query via Web Portal -> ALB -> API Gateway (Cognito OAuth token validated).
2. **Pre-Processing Guardrails**: Query parsed by Presidio (PII redacted) and NeMo Guardrails (checked for prompt injection).
3. **Semantic Cache Check**: Query vector checked against Redis Semantic Cache. On hit (similarity > 0.95), cached response returned immediately (< 100ms).
4. **Hybrid Retrieval**: On cache miss, Query Embedder generates vector -> Searches OpenSearch (Dense HNSW + Sparse BM25, Top-K=5 with Reranker).
5. **LLM Generation**: Context + Prompt dispatched to vLLM on EKS -> Streamed back via SSE while logging telemetry to OpenTelemetry & CloudWatch.

---

## 7. The 10 Crucial Architecture Diagram Views

### 1. Logical Architecture View
End-to-end component data processing flow from document ingestion to query response streaming.

### 2. Infrastructure Architecture View
AWS us-east-1 topology with 3 Availability Zones, Public Subnets (ALB/NAT), Private App Subnets (EKS), and Private Data Subnets (OpenSearch/S3/Redis).

### 3. Security Architecture View
Perimeter WAF -> Cognito Auth -> Presidio PII Filter -> KMS Envelope Encryption -> Row-Level Tenant Vector Isolation.

### 4. Observability, Logging & Monitoring View
OpenTelemetry distributed tracing across API -> Guardrail -> Retriever -> LLM, Prometheus metrics, and Ragas faithfulness tracking.

### 5. MLOps / LLMOps CI/CD Pipeline View
Git Push -> GitHub Actions CI -> Ragas Benchmark Suite -> Model Registry Registration -> ArgoCD Canary Deployment to EKS.

### 6. Data Lineage & Privacy Governance View
Document ingestion lineage tracking (Document ID -> Text Chunks -> Embeddings) + Presidio PII masking for GDPR & EU AI Act compliance.

### 7. Resilience, HA & Multi-Provider Fallback View
Multi-AZ cluster auto-scaling + Fallback Router (Primary vLLM -> Secondary AWS Bedrock -> Local SLM fallback).

### 8. Multi-Agent Orchestration & Tool Execution View
Supervisor Agent -> Retriever Agent -> Summarization Agent -> Citation Verification Agent.

### 9. FinOps & Semantic Cache Cost Optimization View
Redis Semantic Cache (bypasses 30% of LLM calls) + Model Cascading (routing simple lookups to Llama-3-8B and complex prompts to Llama-3-70B).

### 10. AI Model Governance, Safety & HITL Evaluation View
Continuous Ragas evaluation (Faithfulness > 0.90, Answer Relevance > 0.88) + Human-in-the-loop audit review queue for low-confidence scores.

---

## 8. Draw.io Multi-Page XML File
The Draw.io diagram file is available at [`templates/ai_rag_pipeline.drawio`](file:///c:/Users/DELL/Documents/GitHub/ai-solution-architecture/templates/ai_rag_pipeline.drawio).

---

## 9. Infrastructure Architecture Specifications
- **VPC Network**: `10.0.0.0/16` across 3 AZs.
- **EKS Clusters**: 3 Nodes `m6i.xlarge` (Control/Services), 2 Nodes `g5.2xlarge` (vLLM GPU Inference).
- **Databases**: OpenSearch 3-node cluster `r6g.xlarge.search`, ElastiCache Redis `cache.r6g.large`.

---

## 10. Infrastructure as Code (Terraform)
Refer to the skill repository for complete `main.tf` declaration for AWS EKS, VPC, OpenSearch, and KMS resources.

---

## 11. MLOps / LLMOps CI/CD Pipeline
Configured via `.github/workflows/mlops.yml` covering linting, container builds, Ragas evaluation benchmarks, and ArgoCD sync.

---

## 12. Operational & FinOps Model
- **SLA**: 99.9% Availability.
- **Disaster Recovery**: Cross-region S3 replication + OpenSearch snapshots (RPO < 15m, RTO < 1h).
- **FinOps Savings**: Redis caching reduces monthly LLM API costs by ~32%.
