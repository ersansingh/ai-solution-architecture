# Enterprise RAG System Architecture Example

This reference example illustrates the mandatory 12-step architectural response format produced by the `ai-system-design-architect` skill.

---

## 1. AI Problem Classification
- **Category**: Knowledge Retrieval & Generative AI (Enterprise RAG).
- **Use Case**: Secure, role-based Q&A over internal enterprise document repositories (PDFs, Confluence, SharePoint, DBs).

---

## 2. Architecture Pattern Selection
- **Pattern**: Hybrid RAG + Guardrails + Vector DB.
- **Rationale**: Hybrid dense/sparse search (pgvector + BM25) ensures high precision retrieval while NeMo Guardrails prevents prompt injection and hallucinations.

---

## 3. Architecture Reasoning
- **AWS EKS**: Scalable compute for microservices, vLLM inference, and agent runtime.
- **Amazon OpenSearch / pgvector**: High-throughput vector search with HNSW index.
- **Amazon S3**: Secure document lake with KMS encryption.

---

## 4. AI System Context
| Property | Value |
|---|---|
| Business Problem | Fast access to enterprise SOPs and policy docs |
| Users | 25,000 enterprise employees |
| Inference Type | Real-time stream (Server-Sent Events) |
| Latency Target | < 1.5s sub-second first token response |
| Cloud Provider | AWS (Multi-AZ) |

---

## 5. Architecture Components (8 Layers)
1. **User Layer**: Web Portal (React), Slack bot app.
2. **Application Layer**: CloudFront CDN, AWS ALB.
3. **API Layer**: API Gateway, Cognito Auth.
4. **AI Layer**: LangGraph Agent Orchestrator, vLLM Engine, Embedding Service.
5. **Data Layer**: S3 Document Store, OpenSearch Vector Store, Redis Cache.
6. **Security Layer**: KMS, WAF, NeMo Guardrails, IAM Roles.
7. **Infrastructure Layer**: AWS EKS (GPU g5.2xlarge nodes), Private VPC Subnets.
8. **Operations Layer**: Prometheus, Grafana, OpenTelemetry, MLflow Registry.

---

## 6. Interaction Flow
1. User sends query via Web App -> API Gateway authenticates via Cognito.
2. Query passes through Guardrail Filter (PII & Injection scan).
3. Embedding model generates 1536-dim vector -> Queries Vector DB (Top-K=5).
4. Context + Query passed to LLM Inference Service -> Streamed back via SSE.

---

## 7. Architecture Diagrams
*(C4 Container diagram markdown breakdown included here)*

---

## 8. Draw.io XML File
*(Multi-page `.drawio` XML file generated here for import into Draw.io)*

---

## 9. Infrastructure Architecture
- **VPC CIDR**: 10.0.0.0/16
- **Subnets**: 3 Public, 3 Private App, 3 Private Data (3 Availability Zones).

---

## 10. Terraform Infrastructure
*(Executable `main.tf` included here)*

---

## 11. CI/CD Pipeline
*(GitHub Actions `.github/workflows/mlops.yml` included here)*

---

## 12. Operational Model
- **SLA**: 99.9% availability.
- **RPO/RTO**: RPO = 15 mins, RTO = 1 hour.
