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

## 7. Architecture Diagrams (10 Views)

### 1. Logical Architecture View
End-to-end component flow from user interaction through API Gateway, Guardrails, RAG retrieval pipeline, LLM inference, and streaming response. Seven color-coded layer containers (User, Application, Gateway, AI/ML, Data, Security, Ops) with emoji-labeled service cards.

### 2. Infrastructure Architecture View
AWS us-east-1 topology: VPC 10.0.0.0/16 spanning 3 Availability Zones. Public subnets (ALB, NAT Gateway), Private App subnets (EKS worker nodes with CPU and GPU pools), Private Data subnets (OpenSearch, RDS, ElastiCache). Internet Gateway at top, Direct Connect on side.

### 3. Security Architecture View
4-quadrant layout: IAM Federation + Cognito SSO + MFA (top-left), Policy Engine with OPA + GDPR/SOC2 rules (top-right), Audit Logs + SIEM + Security Alerting (bottom-left), Vulnerability Scanner + IDS/IPS + Incident Response (bottom-right). Governance Dashboard bar at bottom.

### 4. Observability, Logging & Monitoring View
4-row layout: Data Collection (Prometheus, cAdvisor, Fluent Bit, OpenTelemetry Collector), Visualization (Grafana dashboards, Elasticsearch/Loki, Kibana, SLA dashboard), Alerting (AlertManager, PagerDuty, Slack, Runbooks), Operations (Auto-scaling HPA/VPA, Self-healing, GitOps ArgoCD, DR backup).

### 5. MLOps / LLMOps CI/CD Pipeline View
Left-to-right pipeline: Git Repo -> CI Pipeline (linting, tests, data validation) -> Model Training (embedding fine-tuning, LLM eval) -> Model Registry (MLflow versioning, approval gate) -> CD Deploy (canary rollout to EKS) -> Monitoring (drift detection, performance). Dashed feedback loop from monitoring back to git for retrain triggers.

### 6. Data Lineage & Privacy Governance View
Document lifecycle: Raw Upload (S3) -> PII Scan (Presidio) -> Masking -> Chunking -> Embedding -> Vector Store (with tenant isolation RLS). Audit trail sidebar tracking lineage from source document to generated answer. GDPR/EU AI Act compliance markers.

### 7. Resilience, HA & Multi-Provider Fallback View
Primary: Azure OpenAI GPT-4 -> Secondary: AWS Bedrock Claude -> Tertiary: Self-hosted vLLM (Llama-3 on EKS GPU). Circuit breaker pattern between providers. Multi-AZ active-active EKS with cross-AZ OpenSearch replication.

### 8. Multi-Agent Orchestration & Tool Execution View
Supervisor LangGraph Agent -> Worker Agents: Search Agent (Vector DB + Web), SQL Agent (PostgreSQL), Code Agent (sandbox execution). Short-term memory (conversation buffer) + Long-term memory (vector persistence). Tool registry with permission boundaries.

### 9. FinOps & Semantic Cache Cost Optimization View
Query flow: Incoming prompt -> Semantic similarity check in Redis GPTCache (cosine > 0.95 = cache hit) -> On miss, route via Model Cascading: simple queries to 8B SLM, complex reasoning to GPT-4/Claude. Per-tenant token quota enforcement. Monthly cost dashboard.

### 10. AI Model Governance, Safety & HITL Evaluation View
Pipeline: Automated Ragas scoring (faithfulness, context recall, answer relevance) -> Confidence threshold check (diamond gate) -> Low-confidence routes to HITL review queue -> Approved answers feed back to fine-tuning dataset. Model Registry stages: Experimental -> Staging -> Candidate -> Production.

---

## 8. Draw.io XML File (Excerpt: 2 of 10 Pages)

The following is a representative excerpt showing 2 complete pages with enterprise-quality styling. The full `.drawio` file contains all 10 view pages.

```xml
<mxfile host="app.diagrams.net" agent="Mozilla/5.0" version="24.0.0" pages="10">
  <!-- Page 1: Logical Architecture -->
  <diagram id="LogicalView" name="1. Logical Architecture">
    <mxGraphModel dx="1600" dy="1100" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Title -->
        <mxCell id="p1_title" value="Enterprise RAG - Logical Architecture" style="text;html=1;fontSize=24;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#1a237e;" vertex="1" parent="1">
          <mxGeometry x="450" y="20" width="500" height="40" as="geometry" />
        </mxCell>
        <!-- User Actor -->
        <mxCell id="p1_user" value="Enterprise&#xa;Users" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#1565c0;strokeColor=#0d47a1;fontColor=#1a237e;fontStyle=1;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="40" y="300" width="50" height="80" as="geometry" />
        </mxCell>
        <!-- Application Layer Container -->
        <mxCell id="p1_app_box" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#43a047;strokeWidth=2;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="140" y="80" width="200" height="350" as="geometry" />
        </mxCell>
        <mxCell id="p1_app_hdr" value="Application Layer" style="text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fillColor=#43a047;strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;" vertex="1" parent="1">
          <mxGeometry x="150" y="90" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="p1_portal" value="🌐 Web Portal&#xa;(React)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#43a047;strokeWidth=1;fontSize=11;fontStyle=0;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="160" y="140" width="160" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_cdn" value="⚡ CloudFront&#xa;CDN" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#43a047;strokeWidth=1;fontSize=11;fontStyle=0;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="160" y="200" width="160" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_alb" value="🔄 Application&#xa;Load Balancer" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#43a047;strokeWidth=1;fontSize=11;fontStyle=0;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="160" y="260" width="160" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_slack" value="💬 Slack Bot&#xa;Integration" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#43a047;strokeWidth=1;fontSize=11;fontStyle=0;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="160" y="320" width="160" height="50" as="geometry" />
        </mxCell>
        <!-- Gateway Layer Container -->
        <mxCell id="p1_gw_box" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#ef6c00;strokeWidth=2;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="380" y="80" width="180" height="350" as="geometry" />
        </mxCell>
        <mxCell id="p1_gw_hdr" value="API Gateway Layer" style="text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fillColor=#ef6c00;strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;" vertex="1" parent="1">
          <mxGeometry x="390" y="90" width="160" height="30" as="geometry" />
        </mxCell>
        <mxCell id="p1_apigw" value="🔐 API Gateway&#xa;(REST/GraphQL)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef6c00;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="395" y="140" width="150" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_auth" value="🛡️ Cognito Auth&#xa;(OAuth2/OIDC)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef6c00;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="395" y="200" width="150" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_rate" value="⚡ Rate Limiting&#xa;&amp; Throttling" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef6c00;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="395" y="260" width="150" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_guard" value="🛡️ NeMo Guardrails&#xa;(PII &amp; Injection)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef6c00;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="395" y="320" width="150" height="50" as="geometry" />
        </mxCell>
        <!-- AI/ML Layer Container -->
        <mxCell id="p1_ai_box" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#0277bd;strokeWidth=2;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="600" y="80" width="220" height="350" as="geometry" />
        </mxCell>
        <mxCell id="p1_ai_hdr" value="AI / ML Layer" style="text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fillColor=#0277bd;strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;" vertex="1" parent="1">
          <mxGeometry x="620" y="90" width="180" height="30" as="geometry" />
        </mxCell>
        <mxCell id="p1_orch" value="🧠 LangGraph&#xa;Orchestrator" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#0277bd;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="620" y="140" width="180" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_embed" value="📐 Embedding Service&#xa;(text-embedding-004)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#0277bd;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="620" y="200" width="180" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_vllm" value="🚀 vLLM Inference&#xa;Engine (GPU)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#0277bd;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="620" y="260" width="180" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p1_rerank" value="🎯 Cross-Encoder&#xa;Reranker" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#0277bd;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="620" y="320" width="180" height="50" as="geometry" />
        </mxCell>
        <!-- Data Layer Container -->
        <mxCell id="p1_data_box" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#7b1fa2;strokeWidth=2;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="860" y="80" width="240" height="350" as="geometry" />
        </mxCell>
        <mxCell id="p1_data_hdr" value="Enterprise Data Platform" style="text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fillColor=#7b1fa2;strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;" vertex="1" parent="1">
          <mxGeometry x="870" y="90" width="220" height="30" as="geometry" />
        </mxCell>
        <mxCell id="p1_opensearch" value="🔍 OpenSearch&#xa;Vector DB" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ffffff;strokeColor=#7b1fa2;strokeWidth=1;fontSize=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="880" y="140" width="100" height="55" as="geometry" />
        </mxCell>
        <mxCell id="p1_s3" value="📦 S3 Document&#xa;Lake (KMS)" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ffffff;strokeColor=#7b1fa2;strokeWidth=1;fontSize=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="990" y="140" width="100" height="55" as="geometry" />
        </mxCell>
        <mxCell id="p1_redis" value="⚡ Redis&#xa;Semantic Cache" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ffffff;strokeColor=#7b1fa2;strokeWidth=1;fontSize=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="880" y="210" width="100" height="55" as="geometry" />
        </mxCell>
        <mxCell id="p1_pg" value="🗄️ PostgreSQL&#xa;Metadata DB" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ffffff;strokeColor=#7b1fa2;strokeWidth=1;fontSize=10;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="990" y="210" width="100" height="55" as="geometry" />
        </mxCell>
        <mxCell id="p1_govern" value="🔐 Data Governance &amp; Lineage" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#7b1fa2;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="880" y="280" width="200" height="40" as="geometry" />
        </mxCell>
        <mxCell id="p1_audit" value="📋 Audit Trail &amp; Compliance" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#7b1fa2;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="880" y="330" width="200" height="40" as="geometry" />
        </mxCell>
        <!-- MLOps Bar -->
        <mxCell id="p1_mlops_bar" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f2f1;strokeColor=#00695c;strokeWidth=2;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="140" y="470" width="960" height="80" as="geometry" />
        </mxCell>
        <mxCell id="p1_mlops_hdr" value="MLOps &amp; LLMOps Platform" style="text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fillColor=#00695c;strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;" vertex="1" parent="1">
          <mxGeometry x="470" y="475" width="220" height="28" as="geometry" />
        </mxCell>
        <mxCell id="p1_mlops1" value="🔄 CI/CD Pipeline" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#00695c;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="160" y="510" width="130" height="30" as="geometry" />
        </mxCell>
        <mxCell id="p1_mlops2" value="📦 Model Registry" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#00695c;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="310" y="510" width="130" height="30" as="geometry" />
        </mxCell>
        <mxCell id="p1_mlops3" value="📊 Model Monitoring" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#00695c;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="460" y="510" width="140" height="30" as="geometry" />
        </mxCell>
        <mxCell id="p1_mlops4" value="🧪 Ragas Evaluation" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#00695c;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="620" y="510" width="140" height="30" as="geometry" />
        </mxCell>
        <mxCell id="p1_mlops5" value="🚀 Canary Deploy" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#00695c;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="780" y="510" width="130" height="30" as="geometry" />
        </mxCell>
        <!-- Infrastructure Bar -->
        <mxCell id="p1_infra_bar" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#eceff1;strokeColor=#455a64;strokeWidth=2;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="140" y="580" width="960" height="60" as="geometry" />
        </mxCell>
        <mxCell id="p1_infra_hdr" value="Infrastructure &amp; Security Layer" style="text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fillColor=#455a64;strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;" vertex="1" parent="1">
          <mxGeometry x="440" y="585" width="280" height="24" as="geometry" />
        </mxCell>
        <mxCell id="p1_infra1" value="☁️ EKS (GPU)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#455a64;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="200" y="612" width="100" height="22" as="geometry" />
        </mxCell>
        <mxCell id="p1_infra2" value="🔐 KMS" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#455a64;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="340" y="612" width="80" height="22" as="geometry" />
        </mxCell>
        <mxCell id="p1_infra3" value="🛡️ WAF" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#455a64;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="460" y="612" width="80" height="22" as="geometry" />
        </mxCell>
        <mxCell id="p1_infra4" value="📊 Prometheus" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#455a64;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="580" y="612" width="100" height="22" as="geometry" />
        </mxCell>
        <mxCell id="p1_infra5" value="📈 Grafana" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#455a64;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="720" y="612" width="100" height="22" as="geometry" />
        </mxCell>
        <mxCell id="p1_infra6" value="🔍 OpenTelemetry" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#455a64;strokeWidth=1;fontSize=10;arcSize=12;shadow=1;" vertex="1" parent="1">
          <mxGeometry x="860" y="612" width="110" height="22" as="geometry" />
        </mxCell>
        <!-- Edges with Labels -->
        <mxCell id="p1_e1" edge="1" source="p1_user" target="p1_portal" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#43a047;strokeWidth=2;endArrow=blockThin;endFill=1;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p1_e1_lbl" connectable="0" parent="p1_e1" value="HTTPS" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontColor=#333333;" vertex="1">
          <mxGeometry relative="1" x="-0.1" as="geometry"><mxPoint as="offset" /></mxGeometry>
        </mxCell>
        <mxCell id="p1_e2" edge="1" source="p1_alb" target="p1_apigw" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ef6c00;strokeWidth=2;endArrow=blockThin;endFill=1;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p1_e2_lbl" connectable="0" parent="p1_e2" value="Route &amp; Auth" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontColor=#333333;" vertex="1">
          <mxGeometry relative="1" x="-0.1" as="geometry"><mxPoint as="offset" /></mxGeometry>
        </mxCell>
        <mxCell id="p1_e3" edge="1" source="p1_apigw" target="p1_orch" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0277bd;strokeWidth=2;endArrow=blockThin;endFill=1;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p1_e3_lbl" connectable="0" parent="p1_e3" value="Validated Query" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontColor=#333333;" vertex="1">
          <mxGeometry relative="1" x="-0.1" as="geometry"><mxPoint as="offset" /></mxGeometry>
        </mxCell>
        <mxCell id="p1_e4" edge="1" source="p1_orch" target="p1_opensearch" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7b1fa2;strokeWidth=2;endArrow=blockThin;endFill=1;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p1_e4_lbl" connectable="0" parent="p1_e4" value="Vector Search&#xa;(Top-K=5)" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontColor=#7b1fa2;" vertex="1">
          <mxGeometry relative="1" x="-0.1" as="geometry"><mxPoint as="offset" /></mxGeometry>
        </mxCell>
        <mxCell id="p1_e5" edge="1" source="p1_orch" target="p1_vllm" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0277bd;strokeWidth=2;endArrow=blockThin;endFill=1;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p1_e5_lbl" connectable="0" parent="p1_e5" value="Context +&#xa;Prompt" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontColor=#0277bd;" vertex="1">
          <mxGeometry relative="1" x="-0.1" as="geometry"><mxPoint as="offset" /></mxGeometry>
        </mxCell>
        <mxCell id="p1_e6" edge="1" source="p1_orch" target="p1_redis" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7b1fa2;strokeWidth=1;dashed=1;endArrow=blockThin;endFill=1;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p1_e6_lbl" connectable="0" parent="p1_e6" value="Cache Check" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=9;fontColor=#999999;fontStyle=2;" vertex="1">
          <mxGeometry relative="1" x="-0.1" as="geometry"><mxPoint as="offset" /></mxGeometry>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 2: Infrastructure Architecture -->
  <diagram id="InfraView" name="2. Infrastructure Architecture">
    <mxGraphModel dx="1600" dy="1300" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1300" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Title -->
        <mxCell id="p2_title" value="Enterprise RAG - AWS Infrastructure (us-east-1)" style="text;html=1;fontSize=24;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#333333;" vertex="1" parent="1">
          <mxGeometry x="350" y="20" width="600" height="40" as="geometry" />
        </mxCell>
        <!-- Internet / Users -->
        <mxCell id="p2_internet" value="Internet / Users" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.internet_alt2;fillColor=#232F3E;strokeColor=#FFFFFF;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="680" y="70" width="60" height="60" as="geometry" />
        </mxCell>
        <!-- AWS Cloud Group -->
        <mxCell id="p2_aws" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=14;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud;stroke=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;" value="AWS Cloud" vertex="1" parent="1">
          <mxGeometry x="50" y="160" width="1320" height="1050" as="geometry" />
        </mxCell>
        <!-- Region -->
        <mxCell id="p2_region" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=13;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;stroke=#147EBA;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=1;" value="Region (us-east-1)" vertex="1" parent="p2_aws">
          <mxGeometry x="30" y="40" width="1260" height="980" as="geometry" />
        </mxCell>
        <!-- VPC -->
        <mxCell id="p2_vpc" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=13;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;stroke=#248814;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;" value="VPC (10.0.0.0/16)" vertex="1" parent="p2_region">
          <mxGeometry x="80" y="50" width="1100" height="880" as="geometry" />
        </mxCell>
        <!-- Internet Gateway -->
        <mxCell id="p2_igw" value="Internet&#xa;Gateway" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.internet_gateway;fillColor=#8C4FFF;strokeColor=#FFFFFF;fontSize=11;fontStyle=1;" vertex="1" parent="p2_vpc">
          <mxGeometry x="500" y="10" width="60" height="60" as="geometry" />
        </mxCell>
        <!-- AZ A -->
        <mxCell id="p2_az_a" value="Availability Zone A (us-east-1a)" style="fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=1;fontColor=#147EBA;fontSize=12;whiteSpace=wrap;html=1;" vertex="1" parent="p2_vpc">
          <mxGeometry x="30" y="90" width="500" height="760" as="geometry" />
        </mxCell>
        <!-- AZ B -->
        <mxCell id="p2_az_b" value="Availability Zone B (us-east-1b)" style="fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=1;fontColor=#147EBA;fontSize=12;whiteSpace=wrap;html=1;" vertex="1" parent="p2_vpc">
          <mxGeometry x="570" y="90" width="500" height="760" as="geometry" />
        </mxCell>
        <!-- Public Subnet A -->
        <mxCell id="p2_pub_a" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#248814;fillColor=#E9F3E6;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;" value="Public Subnet A&#xa;(10.0.1.0/24)" vertex="1" parent="p2_vpc">
          <mxGeometry x="60" y="130" width="440" height="140" as="geometry" />
        </mxCell>
        <!-- Public Subnet B -->
        <mxCell id="p2_pub_b" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#248814;fillColor=#E9F3E6;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;" value="Public Subnet B&#xa;(10.0.2.0/24)" vertex="1" parent="p2_vpc">
          <mxGeometry x="600" y="130" width="440" height="140" as="geometry" />
        </mxCell>
        <!-- Private App Subnet A -->
        <mxCell id="p2_priv_a" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#DF8600;fillColor=#FFF2CC;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;" value="Private App Subnet A&#xa;(10.0.4.0/24)" vertex="1" parent="p2_vpc">
          <mxGeometry x="60" y="310" width="440" height="200" as="geometry" />
        </mxCell>
        <!-- Private App Subnet B -->
        <mxCell id="p2_priv_b" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#DF8600;fillColor=#FFF2CC;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;" value="Private App Subnet B&#xa;(10.0.5.0/24)" vertex="1" parent="p2_vpc">
          <mxGeometry x="600" y="310" width="440" height="200" as="geometry" />
        </mxCell>
        <!-- Database Subnet A -->
        <mxCell id="p2_db_a" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#DD3522;fillColor=#FFCCCC;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;" value="Database Subnet A&#xa;(10.0.7.0/24)" vertex="1" parent="p2_vpc">
          <mxGeometry x="60" y="560" width="440" height="170" as="geometry" />
        </mxCell>
        <!-- Database Subnet B -->
        <mxCell id="p2_db_b" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=11;fontStyle=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#DD3522;fillColor=#FFCCCC;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;" value="Database Subnet B&#xa;(10.0.8.0/24)" vertex="1" parent="p2_vpc">
          <mxGeometry x="600" y="560" width="440" height="170" as="geometry" />
        </mxCell>
        <!-- NAT Gateways -->
        <mxCell id="p2_nat_a" value="NAT Gateway" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.nat_gateway;fillColor=#8C4FFF;strokeColor=#FFFFFF;fontSize=10;" vertex="1" parent="p2_pub_a">
          <mxGeometry x="30" y="40" width="50" height="50" as="geometry" />
        </mxCell>
        <!-- ALBs -->
        <mxCell id="p2_alb_a" value="Application&#xa;Load Balancer" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elasticloadbalancing;fillColor=#8C4FFF;strokeColor=#FFFFFF;fontSize=10;" vertex="1" parent="p2_pub_a">
          <mxGeometry x="300" y="40" width="50" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p2_nat_b" value="NAT Gateway" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.nat_gateway;fillColor=#8C4FFF;strokeColor=#FFFFFF;fontSize=10;" vertex="1" parent="p2_pub_b">
          <mxGeometry x="30" y="40" width="50" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p2_alb_b" value="Application&#xa;Load Balancer" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elasticloadbalancing;fillColor=#8C4FFF;strokeColor=#FFFFFF;fontSize=10;" vertex="1" parent="p2_pub_b">
          <mxGeometry x="300" y="40" width="50" height="50" as="geometry" />
        </mxCell>
        <!-- EKS Cluster + Workers in Private Subnets -->
        <mxCell id="p2_eks" value="EKS Cluster" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;" vertex="1" parent="p2_priv_a">
          <mxGeometry x="30" y="50" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="p2_worker1" value="CPU Worker&#xa;Node" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="p2_priv_a">
          <mxGeometry x="170" y="55" width="48" height="48" as="geometry" />
        </mxCell>
        <mxCell id="p2_worker2" value="GPU Worker&#xa;(g5.2xlarge)" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="p2_priv_a">
          <mxGeometry x="300" y="55" width="48" height="48" as="geometry" />
        </mxCell>
        <mxCell id="p2_worker3" value="CPU Worker&#xa;Node" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="p2_priv_b">
          <mxGeometry x="100" y="55" width="48" height="48" as="geometry" />
        </mxCell>
        <mxCell id="p2_worker4" value="GPU Worker&#xa;(g5.2xlarge)" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="p2_priv_b">
          <mxGeometry x="270" y="55" width="48" height="48" as="geometry" />
        </mxCell>
        <!-- Database Resources -->
        <mxCell id="p2_opensearch" value="OpenSearch&#xa;(Primary)" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elasticsearch_service;fillColor=#8C4FFF;strokeColor=#FFFFFF;fontSize=10;" vertex="1" parent="p2_db_a">
          <mxGeometry x="100" y="50" width="50" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p2_rds_primary" value="RDS PostgreSQL&#xa;(Primary)" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;fillColor=#C925D1;strokeColor=#FFFFFF;fontSize=10;" vertex="1" parent="p2_db_a">
          <mxGeometry x="280" y="50" width="50" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p2_elasticache" value="ElastiCache&#xa;Redis" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elasticache;fillColor=#C925D1;strokeColor=#FFFFFF;fontSize=10;" vertex="1" parent="p2_db_b">
          <mxGeometry x="100" y="50" width="50" height="50" as="geometry" />
        </mxCell>
        <mxCell id="p2_rds_standby" value="RDS PostgreSQL&#xa;(Standby)" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds;fillColor=#C925D1;strokeColor=#FFFFFF;fontSize=10;" vertex="1" parent="p2_db_b">
          <mxGeometry x="280" y="50" width="50" height="50" as="geometry" />
        </mxCell>
        <!-- Edges -->
        <mxCell id="p2_e1" edge="1" source="p2_internet" target="p2_igw" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#232F3E;strokeWidth=2;fillColor=none;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p2_e2" edge="1" source="p2_alb_a" target="p2_worker1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ED7100;strokeWidth=2;fillColor=none;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p2_e3" edge="1" source="p2_alb_a" target="p2_worker2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ED7100;strokeWidth=2;fillColor=none;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p2_e4" edge="1" source="p2_worker1" target="p2_opensearch" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#C925D1;strokeWidth=2;fillColor=none;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p2_e5" edge="1" source="p2_worker2" target="p2_rds_primary" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#C925D1;strokeWidth=2;fillColor=none;" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="p2_e6" edge="1" source="p2_rds_primary" target="p2_rds_standby" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#C925D1;strokeWidth=2;dashed=1;fillColor=none;fontSize=10;fontStyle=2;" value="Replication" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Pages 3-10 follow the same quality patterns for Security, Observability, MLOps, Data Governance, Resilience, Multi-Agent, FinOps, and Model Governance views -->
</mxfile>
```

---

## 9. Infrastructure Architecture

### Network Topology
| Component | Specification |
|---|---|
| **VPC CIDR** | 10.0.0.0/16 |
| **Region** | us-east-1 (N. Virginia) |
| **Availability Zones** | us-east-1a, us-east-1b, us-east-1c |

### Subnet Layout (3 AZs x 3 Tiers = 9 Subnets)
| Tier | AZ-a | AZ-b | AZ-c | Purpose |
|---|---|---|---|---|
| **Public** | 10.0.1.0/24 | 10.0.2.0/24 | 10.0.3.0/24 | ALB, NAT Gateway, Bastion |
| **Private App** | 10.0.4.0/24 | 10.0.5.0/24 | 10.0.6.0/24 | EKS Worker Nodes |
| **Private Data** | 10.0.7.0/24 | 10.0.8.0/24 | 10.0.9.0/24 | RDS, OpenSearch, ElastiCache |

### Compute
| Cluster | Node Group | Instance Type | Min/Max | Purpose |
|---|---|---|---|---|
| EKS `rag-prod` | `cpu-general` | m6i.xlarge | 3 / 12 | API, orchestration, embedding |
| EKS `rag-prod` | `gpu-inference` | g5.2xlarge | 2 / 8 | vLLM inference, reranker |

### Storage & Data
- **S3**: `rag-doc-lake-prod` (KMS CMK encrypted, versioning enabled, lifecycle 90d to Glacier)
- **OpenSearch**: 3-node cluster (r6g.xlarge.search), HNSW index, 1536-dim vectors
- **RDS PostgreSQL**: Multi-AZ db.r6g.large, encrypted at rest, automated backups 7d retention
- **ElastiCache Redis**: 2-node cluster (cache.r6g.large), in-transit encryption, semantic cache

---

## 10. Terraform Infrastructure

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "rag-prod-vpc"
  cidr = "10.0.0.0/16"

  azs              = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnets  = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
  database_subnets = ["10.0.7.0/24", "10.0.8.0/24", "10.0.9.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true

  tags = { Environment = "production", Project = "enterprise-rag" }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "rag-prod"
  cluster_version = "1.30"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  eks_managed_node_groups = {
    cpu_general = {
      instance_types = ["m6i.xlarge"]
      min_size       = 3
      max_size       = 12
      desired_size   = 3
    }
    gpu_inference = {
      instance_types = ["g5.2xlarge"]
      min_size       = 2
      max_size       = 8
      desired_size   = 2
      ami_type       = "AL2_x86_64_GPU"
    }
  }
}
```

---

## 11. CI/CD Pipeline

```yaml
name: RAG MLOps Pipeline
on:
  push:
    branches: [main]
    paths: ['models/**', 'embeddings/**', 'config/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint & Unit Tests
        run: make test
      - name: Data Validation (Great Expectations)
        run: make validate-data

  train-eval:
    needs: validate
    runs-on: [self-hosted, gpu]
    steps:
      - name: Fine-tune Embeddings
        run: python train/finetune_embeddings.py --config config/embed.yaml
      - name: Evaluate with Ragas
        run: python eval/ragas_benchmark.py --threshold 0.85
      - name: Register Model (MLflow)
        run: python registry/register_model.py --stage staging

  deploy:
    needs: train-eval
    runs-on: ubuntu-latest
    steps:
      - name: Canary Deploy to EKS
        run: kubectl apply -f k8s/canary-deployment.yaml
      - name: Smoke Tests
        run: make integration-test
      - name: Promote to Production
        run: kubectl apply -f k8s/production-deployment.yaml
```

---

## 12. Operational Model

| Parameter | Specification |
|---|---|
| **SLA** | 99.9% availability (43.8 min/month max downtime) |
| **RPO** | 15 minutes (S3 versioning + RDS continuous backup) |
| **RTO** | 1 hour (EKS multi-AZ auto-recovery + RDS failover) |
| **Latency SLO** | TTFT < 800ms (P95), total response < 5s (P95) |
| **Throughput** | 200 RPS peak, 50 RPS sustained |

### Cost Estimate (Monthly)
| Component | Specification | Est. Cost |
|---|---|---|
| EKS Cluster | Control plane + 3 CPU + 2 GPU nodes | $2,400 |
| OpenSearch | 3x r6g.xlarge.search | $1,200 |
| RDS PostgreSQL | Multi-AZ db.r6g.large | $450 |
| ElastiCache Redis | 2x cache.r6g.large | $400 |
| S3 + Data Transfer | 500GB storage + egress | $150 |
| LLM API (fallback) | Azure OpenAI 2M tokens/month | $200 |
| **Total** | | **~$4,800/mo** |

### Disaster Recovery
- **Strategy**: Active-Passive Multi-AZ with automated RDS failover.
- **Backup**: Daily EBS snapshots, S3 cross-region replication to us-west-2, RDS automated backups (7-day retention).
- **Runbook**: Automated PagerDuty escalation -> On-call SRE -> Runbook execution -> Post-mortem within 48h.
