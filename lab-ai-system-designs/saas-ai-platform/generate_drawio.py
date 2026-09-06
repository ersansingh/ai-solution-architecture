import html
import os

def create_drawio_xml():
    diagrams = []

    # Helper for XML escaping
    def esc(text):
        return html.escape(text).replace('\n', '&#10;')

    # Helper for node
    def node(cell_id, label, x, y, w, h, style, parent="1"):
        return f'<mxCell id="{cell_id}" value="{esc(label)}" style="{style}" vertex="1" parent="{parent}">\n  <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />\n</mxCell>'

    # Helper for edge
    def edge(edge_id, source, target, label="", style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthoLoop=1;jettySize=auto;html=1;strokeColor=#3b82f6;strokeWidth=2;fontSize=9;", parent="1"):
        lbl = f'value="{esc(label)}"' if label else 'value=""'
        return f'<mxCell id="{edge_id}" {lbl} style="{style}" edge="1" parent="{parent}" source="{source}" target="{target}">\n  <mxGeometry relative="1" as="geometry" />\n</mxCell>'

    # Helper for swimlane / container
    def lane(lane_id, title, x, y, w, h, style="swimlane;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#cbd5e1;fontStyle=1;startSize=28;rounded=1;fontSize=11;fontColor=#334155;", parent="1"):
        return f'<mxCell id="{lane_id}" value="{esc(title)}" style="{style}" vertex="1" parent="{parent}">\n  <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />\n</mxCell>'

    # =========================================================================
    # 1. LOGICAL ARCHITECTURE VIEW (Cloud Agnostic AI Platform + OTel & Observe & Obstack)
    # =========================================================================
    p1 = []
    p1.append(node("p1_title", "Multi-Region Enterprise SaaS AI Platform — End-to-End Logical Architecture", 300, 10, 1000, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    # Lane 1: Client & Global Ingress
    p1.append(lane("p1_l1", "1. Global Omnichannel Ingress & Edge Layer (Anycast DNS & CloudFront)", 30, 55, 1540, 95, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p1.append(node("p1_web", "SaaS Web Portal\n(React / Next.js)", 20, 35, 150, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p1_l1"))
    p1.append(node("p1_mobile", "Mobile Copilot\n(iOS / Android)", 190, 35, 150, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p1_l1"))
    p1.append(node("p1_ext", "Enterprise Integrations\n(Slack / MS Teams / API)", 360, 35, 180, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p1_l1"))
    p1.append(node("p1_r53", "AWS Route 53 (GeoDNS)\n& CloudFront Anycast Edge", 560, 35, 190, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l1"))
    p1.append(node("p1_edge_wasm", "CloudFront Functions & WASM\nEdge Token & Tenant Routing", 770, 35, 210, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l1"))
    p1.append(node("p1_privatelink", "AWS PrivateLink Ingress\n(Enterprise B2B VPC Peering)", 1000, 35, 200, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#e0e7ff;strokeColor=#6366f1;fontStyle=1;fontSize=10;shadow=1;", "p1_l1"))
    p1.append(node("p1_waf", "AWS WAF & DDoS Shield\n(OWASP Top 10 + Rate Limits)", 1220, 35, 200, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p1_l1"))

    # Lane 2: Regional Security & API Gateway Layer
    p1.append(lane("p1_l2", "2. Regional Security, Tenant Context & Gateway Layer (5 Global Regional Hubs)", 30, 165, 1540, 105, "swimlane;whiteSpace=wrap;html=1;fillColor=#fef2f2;strokeColor=#ef4444;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#991b1b;"))
    p1.append(node("p1_alb", "Regional ALB / Kong Gateway\n(TLS 1.3 Termination)", 20, 36, 190, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p1_l2"))
    p1.append(node("p1_auth", "IAM Identity Center / OIDC\nTenant ABAC Token Validator", 230, 36, 200, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p1_l2"))
    p1.append(node("p1_presidio", "Presidio PII Redaction Engine\n(In-flight Anonymization)", 450, 36, 200, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p1_l2"))
    p1.append(node("p1_guardrails", "NeMo & Bedrock Guardrails\n(Prompt Injection & Topic Jailbreak)", 670, 36, 220, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p1_l2"))
    p1.append(node("p1_sem_cache", "ElastiCache Redis Semantic Cache\n(Cosine Sim >= 0.95 -> <20ms Hit)", 910, 32, 230, 60, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l2"))
    p1.append(node("p1_rate_quota", "Tenant Rate Limiter & Token Quota\n(Fair-share Tiered Throttling)", 1160, 36, 220, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p1_l2"))

    # Lane 3: AI Agent Orchestration & Copilot Runtime
    p1.append(lane("p1_l3", "3. Copilot Runtime & Multi-Agent Orchestration Layer (Bedrock AgentCore & EKS)", 30, 285, 1540, 115, "swimlane;whiteSpace=wrap;html=1;fillColor=#f5f3ff;strokeColor=#8b5cf6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#5b21b6;"))
    p1.append(node("p1_agentcore", "Bedrock AgentCore Orchestrator\n(Task Decomposition & Plan)", 20, 36, 210, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p1_l3"))
    p1.append(node("p1_rag_agent", "Enterprise RAG Agent\n(Context Retrieval & Rerank)", 250, 36, 190, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p1_l3"))
    p1.append(node("p1_tool_agent", "Tool Execution & API Agent\n(CRM / ERP / Workflow APIs)", 460, 36, 200, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p1_l3"))
    p1.append(node("p1_code_agent", "Code & Analytics Agent\n(Isolated WASM/Firecracker Sandbox)", 680, 36, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p1_l3"))
    p1.append(node("p1_routing_tier", "Model Router & Cascading Engine\n(SLM 8B vs Frontier LLM)", 920, 36, 210, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p1_l3"))
    p1.append(node("p1_mem_state", "Agent Session State & Memory\n(DynamoDB Global + Redis)", 1150, 32, 210, 68, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p1_l3"))

    # Lane 4: AI Model Serving & Compute Pools (Karpenter & KEDA)
    p1.append(lane("p1_l4", "4. Regional Compute & Model Serving Pools (EKS Autoscaled GPU / Inferentia / Graviton)", 30, 415, 1540, 115, "swimlane;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#f59e0b;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#b45309;"))
    p1.append(node("p1_vllm_l4", "vLLM Inference Cluster\n(AWS G6 L4 GPUs — Sub-150ms)", 20, 36, 210, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l4"))
    p1.append(node("p1_inf2", "AWS Inferentia2 (Inf2) Fleet\n(Embeddings & Fast Reranking)", 250, 36, 200, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l4"))
    p1.append(node("p1_bedrock_api", "Managed Amazon Bedrock\n(Claude 3.5 Sonnet / Haiku)", 470, 36, 200, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l4"))
    p1.append(node("p1_warm_pools", "Warm Pools & Pre-warmed GPUs\n(Zero Cold Start on 3x Surge)", 690, 36, 210, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l4"))
    p1.append(node("p1_trainium_spot", "Trainium / H100 Spot Pool\n(60% Spot Finetuning & Training)", 920, 36, 210, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l4"))
    p1.append(node("p1_karpenter", "Karpenter + KEDA Controller\n(Dynamic Scale-to-Zero & Bin-packing)", 1150, 36, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l4"))

    # Lane 5: Tiered Storage, Multi-Tenant Vector DB & Data Lake
    p1.append(lane("p1_l5", "5. Tiered Storage & Multi-Tenant RAG Data Layer (Tenant Isolation & Vector DB)", 30, 545, 1540, 115, "swimlane;whiteSpace=wrap;html=1;fillColor=#ecfdf5;strokeColor=#10b981;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#065f46;"))
    p1.append(node("p1_opensearch", "Amazon OpenSearch Serverless\n(Multi-Tenant Vector Search + RLS)", 20, 32, 230, 68, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p1_l5"))
    p1.append(node("p1_aurora", "Aurora PostgreSQL Global DB\n(Tenant Metadata, RLS & pgvector)", 270, 32, 220, 68, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p1_l5"))
    p1.append(node("p1_s3_tables", "Amazon S3 Tables / Iceberg\n(Analytics, Knowledge Lake & Chunks)", 510, 32, 220, 68, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p1_l5"))
    p1.append(node("p1_fsx", "Amazon FSx for Lustre\n(Ultra-fast Checkpoints & Datasets)", 750, 32, 210, 68, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p1_l5"))
    p1.append(node("p1_kms", "AWS KMS Tenant-Keyed CMKs\n(BYOK Envelope Encryption at Rest)", 980, 36, 210, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p1_l5"))
    p1.append(node("p1_lineage", "Apache Atlas / DataZone\n(Data Lineage & GDPR Purge)", 1210, 36, 210, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p1_l5"))

    # Lane 6: Cloud-Agnostic Observability, FinOps & Governance Layer (OTel Gateway + Observe Inc + Obstack)
    p1.append(lane("p1_l6", "6. Unified Cloud-Agnostic Observability Layer (OTel Gateway, Observe Inc. Logs & Obstack Metrics)", 30, 675, 1540, 100, "swimlane;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#64748b;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e293b;"))
    p1.append(node("p1_otel", "Cloud-Agnostic OTel Gateway\n(OTLP Dual-Tier Ingress & Redaction)", 20, 34, 230, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p1_l6"))
    p1.append(node("p1_observe_logs", "Observe Inc. (Logs & Tracing)\n(OPAL Log Modeling & Span Graphs)", 270, 34, 230, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p1_l6"))
    p1.append(node("p1_obstack_metrics", "Obstack (Prometheus TSDB)\n(High-Cardinality Metrics & Alerts)", 520, 34, 230, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p1_l6"))
    p1.append(node("p1_journey_metrics", "Customer Journey & Biz Telemetry\n(Funnel, CSAT, DACU, Token Spend)", 770, 34, 240, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p1_l6"))
    p1.append(node("p1_grafana_unified", "Grafana Enterprise Single-Pane\n(Multi-Tenant SLOs & FinOps)", 1030, 34, 230, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#64748b;fontStyle=1;fontSize=10;shadow=1;", "p1_l6"))
    p1.append(node("p1_audit", "Tamper-proof Compliance Vault\n(SOC2 Type II / ISO 27001 Audit)", 1280, 34, 240, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p1_l6"))

    # Connectors for Page 1
    p1.append(edge("e1_1", "p1_r53", "p1_alb", "HTTPS / TLS 1.3"))
    p1.append(edge("e1_2", "p1_alb", "p1_auth", "JWT & Tenant ABAC"))
    p1.append(edge("e1_3", "p1_auth", "p1_guardrails", "Sanitized Prompt"))
    p1.append(edge("e1_4", "p1_guardrails", "p1_sem_cache", "Check Cache"))
    p1.append(edge("e1_5", "p1_guardrails", "p1_agentcore", "Cache Miss -> Orchestrate"))
    p1.append(edge("e1_6", "p1_agentcore", "p1_rag_agent", "Retrieve Knowledge"))
    p1.append(edge("e1_7", "p1_rag_agent", "p1_opensearch", "Tenant-Isolated Vector Query"))
    p1.append(edge("e1_8", "p1_agentcore", "p1_routing_tier", "Optimized Prompt"))
    p1.append(edge("e1_9", "p1_routing_tier", "p1_vllm_l4", "Sub-150ms Local Inference"))
    p1.append(edge("e1_10", "p1_routing_tier", "p1_bedrock_api", "Complex Frontier Reasoning"))
    p1.append(edge("e1_11", "p1_vllm_l4", "p1_otel", "OTLP Telemetry Streams"))
    p1.append(edge("e1_12", "p1_otel", "p1_observe_logs", "Logs & Traces"))
    p1.append(edge("e1_13", "p1_otel", "p1_obstack_metrics", "Prometheus Remote Write"))

    diagrams.append(('LogicalView', '1. Logical Architecture', p1))

    # =========================================================================
    # 2. INFRASTRUCTURE ARCHITECTURE VIEW (5 Global Regions + Control Plane)
    # =========================================================================
    p2 = []
    p2.append(node("p2_title", "Global Multi-Region AWS Infrastructure Architecture (5 Regional Hubs + Control Plane)", 250, 10, 1100, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    # Global Edge & Control Plane Container
    p2.append(lane("p2_global", "AWS Global Control Plane & Edge Services (AWS Organizations & Control Tower)", 30, 55, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p2.append(node("p2_g_r53", "Amazon Route 53\n(Latency & Geoproximity Routing)", 20, 36, 210, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p2_global"))
    p2.append(node("p2_g_cf", "Amazon CloudFront Edge\n(Global Points of Presence)", 250, 36, 200, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p2_global"))
    p2.append(node("p2_g_org", "AWS Organizations & Control Tower\n(Multi-Account Governance & SCPs)", 470, 36, 230, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p2_global"))
    p2.append(node("p2_g_iam", "IAM Identity Center\n(Global Tenant Directory & ABAC)", 720, 36, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p2_global"))
    p2.append(node("p2_g_bedrock", "Central Bedrock Model Registry\n(Approved Weights & Guardrail Specs)", 960, 36, 230, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p2_global"))
    p2.append(node("p2_g_transit", "AWS Transit Gateway Global Router\n(Cross-Region Interconnect)", 1210, 36, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p2_global"))

    # Regional Hub 1: us-east-1 (Primary Americas)
    p2.append(lane("p2_reg1", "Regional Hub 1: US-East (N. Virginia) — Production EKS AI Hub", 30, 190, 750, 270, "swimlane;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p2.append(node("p2_r1_vpc", "Regional VPC (10.100.0.0/16) — 3 AZs\nPublic / Private App / Private GPU / Secure Data", 20, 36, 710, 40, "rounded=1;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;", "p2_reg1"))
    p2.append(node("p2_r1_eks", "Amazon EKS Cluster v1.30\n(Control Plane & Core Services)", 20, 85, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p2_reg1"))
    p2.append(node("p2_r1_karp", "Karpenter Autoscaler\n(g6.2xlarge L4 & inf2.8xlarge)", 260, 85, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p2_reg1"))
    p2.append(node("p2_r1_spot", "Spot Worker Pool (Trainium / H100)\n(60% Spot Finetuning Nodes)", 500, 85, 230, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p2_reg1"))
    p2.append(node("p2_r1_os", "OpenSearch Vector Serverless\n(Dedicated Collection per Tenant)", 20, 155, 220, 60, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p2_reg1"))
    p2.append(node("p2_r1_aurora", "Aurora PostgreSQL Global (Primary)\n(Storage Autoscaling & RLS)", 260, 155, 220, 60, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p2_reg1"))
    p2.append(node("p2_r1_cache", "ElastiCache Redis Cluster\n(Semantic Prompt Cache)", 500, 155, 230, 60, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p2_reg1"))
    p2.append(node("p2_r1_fsx", "FSx for Lustre (Shared Fast FS)\n(100 GB/s Checkpoint Streaming)", 20, 222, 710, 36, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;", "p2_reg1"))

    # Regional Hub 2: eu-west-1 (Europe Hub — Sovereign & GDPR)
    p2.append(lane("p2_reg2", "Regional Hub 2: EU-West (Ireland) — Sovereign European AI Hub (GDPR)", 820, 190, 750, 270, "swimlane;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#10b981;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#065f46;"))
    p2.append(node("p2_r2_vpc", "Regional VPC (10.101.0.0/16) — 3 AZs\nStrict EU Data Boundary & Local KMS CMKs", 20, 36, 710, 40, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ecfdf5;strokeColor=#10b981;fontStyle=1;fontSize=10;", "p2_reg2"))
    p2.append(node("p2_r2_eks", "Amazon EKS Cluster v1.30\n(EU Regional Inference Hub)", 20, 85, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p2_reg2"))
    p2.append(node("p2_r2_karp", "Karpenter Autoscaler\n(Warm L4 / Graviton Pools)", 260, 85, 220, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p2_reg2"))
    p2.append(node("p2_r2_spot", "Spot Worker Pool (Trainium)\n(Local EU Embeddings Batch)", 500, 85, 230, 60, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p2_reg2"))
    p2.append(node("p2_r2_os", "OpenSearch Vector Serverless\n(EU Data Resident Vectors)", 20, 155, 220, 60, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p2_reg2"))
    p2.append(node("p2_r2_aurora", "Aurora PostgreSQL Global (Replica)\n(Local Read Replica & RLS)", 260, 155, 220, 60, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p2_reg2"))
    p2.append(node("p2_r2_cache", "ElastiCache Redis Cluster\n(Local EU Prompt Cache)", 500, 155, 230, 60, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p2_reg2"))
    p2.append(node("p2_r2_fsx", "FSx for Lustre (EU Local)\n(Sovereign Checkpoint Cache)", 20, 222, 710, 36, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;", "p2_reg2"))

    # Regional Hubs 3, 4, 5 Summary Row
    p2.append(lane("p2_reg_other", "Regional Hubs 3, 4, 5: APAC & US-West (ap-southeast-1, ap-northeast-1, us-west-2)", 30, 475, 1540, 180, "swimlane;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#64748b;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e293b;"))
    p2.append(node("p2_r3", "Hub 3: AP-Southeast (Singapore)\n• EKS vLLM Inference Hub (L4 GPUs)\n• OpenSearch Vector Replica\n• ElastiCache Semantic Cache\n• Latency Target: <120ms SEA", 20, 36, 470, 130, "rounded=1;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p2_reg_other"))
    p2.append(node("p2_r4", "Hub 4: AP-Northeast (Tokyo)\n• EKS vLLM Inference Hub (L4 GPUs)\n• OpenSearch Vector Replica\n• ElastiCache Semantic Cache\n• Latency Target: <110ms Japan/KR", 510, 36, 470, 130, "rounded=1;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p2_reg_other"))
    p2.append(node("p2_r5", "Hub 5: US-West (Oregon)\n• EKS vLLM Inference Hub (L4 GPUs)\n• OpenSearch Vector Replica\n• ElastiCache Semantic Cache\n• Secondary Training / Spot Failover", 1000, 36, 470, 130, "rounded=1;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p2_reg_other"))

    # Cross-Region Data Sync Layer
    p2.append(lane("p2_sync", "Cross-Region Replication & Global Data Sync Layer", 30, 670, 1540, 95, "swimlane;whiteSpace=wrap;html=1;fillColor=#ecfdf5;strokeColor=#10b981;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#065f46;"))
    p2.append(node("p2_s_s3", "Amazon S3 Multi-Region Access Points\n(Cross-Region Replication & Tables)", 20, 35, 340, 48, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p2_sync"))
    p2.append(node("p2_s_aurora", "Aurora Global Database Replication Engine\n(<1 sec Cross-Region Storage Replication)", 380, 35, 360, 48, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p2_sync"))
    p2.append(node("p2_s_secrets", "AWS Secrets Manager & KMS Multi-Region Keys\n(Synchronized Secrets & BYOK Keys)", 760, 35, 360, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p2_sync"))
    p2.append(node("p2_s_mesh", "AWS App Mesh / Cilium Multi-Cluster Mesh\n(Cross-Region mTLS Zero-Trust Routing)", 1140, 35, 340, 48, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p2_sync"))

    diagrams.append(('InfraView', '2. Infrastructure Architecture', p2))

    # =========================================================================
    # 3. SECURITY ARCHITECTURE VIEW
    # =========================================================================
    p3 = []
    p3.append(node("p3_title", "Enterprise AI Security, Multi-Tenant ABAC & AI Safety Architecture", 250, 10, 1100, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    p3.append(lane("p3_l1", "1. Perimeter & Identity Security (Zero-Trust Ingress)", 30, 55, 1540, 110, "swimlane;whiteSpace=wrap;html=1;fillColor=#fef2f2;strokeColor=#ef4444;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#991b1b;"))
    p3.append(node("p3_waf", "AWS WAF AI Ruleset\n(SQLi, XSS, IP Reputation)", 20, 36, 210, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p3_l1"))
    p3.append(node("p3_idp", "Enterprise IdP (Okta / Azure AD)\n(SAML 2.0 / OIDC Federation)", 250, 36, 230, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p3_l1"))
    p3.append(node("p3_jwt", "JWT / OIDC Token Verification\n(Claims: tenant_id, role, clearance)", 500, 36, 240, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p3_l1"))
    p3.append(node("p3_abac", "AWS Cedar / OPA ABAC Policy Engine\n(Contextual Dynamic Permission Check)", 760, 36, 260, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p3_l1"))
    p3.append(node("p3_mtls", "Istio / Cilium mTLS SPIFFE/SPIRE\n(Zero-Trust Pod-to-Pod Identity)", 1040, 36, 240, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p3_l1"))
    p3.append(node("p3_sec_group", "Private Subnet Network Policies\n(Strict Egress / Ingress Firewalls)", 1300, 36, 210, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p3_l1"))

    p3.append(lane("p3_l2", "2. Generative AI Input/Output Guardrails & Privacy Sanitization", 30, 185, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#b45309;"))
    p3.append(node("p3_presidio_in", "Microsoft Presidio (Input)\n• Detect PII, SSN, Credit Cards\n• Cryptographic Token Replacement", 20, 36, 260, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p3_l2"))
    p3.append(node("p3_nemo_in", "NeMo Guardrails & Llama Guard\n• Prompt Injection Classifier\n• Jailbreak / Indirect Injection Block", 300, 36, 270, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p3_l2"))
    p3.append(node("p3_topic_filter", "Topic & Safety Boundary Filter\n• Competitor & Profanity Filter\n• SaaS Domain Scope Enforcer", 590, 36, 260, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p3_l2"))
    p3.append(node("p3_nemo_out", "Output Hallucination & PII Filter\n• Verify Citation Grounding\n• Mask Extracted Sensitive Data", 870, 36, 270, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p3_l2"))
    p3.append(node("p3_sandbox", "Firecracker MicroVM Sandbox\n• Safe Agent Tool Execution\n• Zero Network Egress for Code Tools", 1160, 36, 270, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p3_l2"))

    p3.append(lane("p3_l3", "3. Multi-Tenant Data Isolation & Cryptographic Partitioning", 30, 325, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#ecfdf5;strokeColor=#10b981;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#065f46;"))
    p3.append(node("p3_kms_cmk", "AWS KMS Tenant-Keyed CMKs\n(BYOK / HYOK Encryption Envelope)", 20, 36, 260, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p3_l3"))
    p3.append(node("p3_os_sec", "OpenSearch Tenant Security\n• Dedicated Index / Namespace\n• Document & Field-Level Security", 300, 36, 270, 68, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p3_l3"))
    p3.append(node("p3_aurora_rls", "Aurora PostgreSQL RLS\n• Row-Level Security: tenant_id\n• Tenant DB User Session Injection", 590, 36, 260, 68, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p3_l3"))
    p3.append(node("p3_s3_prefix", "S3 Bucket Prefix Isolation\n• KMS Key per Tenant Prefix\n• Strict IAM S3 Policy Conditions", 870, 36, 270, 68, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p3_l3"))
    p3.append(node("p3_vault", "HashiCorp Vault / Secrets Manager\n(Dynamic DB Credentials & API Keys)", 1160, 36, 270, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p3_l3"))

    p3.append(lane("p3_l4", "4. Compliance, Auditability & Evidence Collection (SOC2 Type II & ISO 27001)", 30, 465, 1540, 105, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p3.append(node("p3_audit_trail", "AWS CloudTrail & VPC Flow Logs\n(Immutable S3 Glacier Vault)", 20, 36, 280, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p3_l4"))
    p3.append(node("p3_guardduty", "Amazon GuardDuty + AI Threat Detection\n(Anomalous API & IAM Spike Detection)", 320, 36, 300, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p3_l4"))
    p3.append(node("p3_securityhub", "AWS Security Hub & CIS Benchmarks\n(Automated Continuous Compliance Audit)", 640, 36, 300, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p3_l4"))
    p3.append(node("p3_model_audit", "Model Decision & Prompt Audit Logger\n(Anonymized Audit Trails for Regulators)", 960, 36, 300, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p3_l4"))
    p3.append(node("p3_soc2_dash", "SOC2 / ISO 27001 Live Dashboard\n(Real-time Compliance Posture)", 1280, 36, 230, 52, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p3_l4"))

    diagrams.append(('SecurityView', '3. Security Architecture', p3))

    # =========================================================================
    # 4. OBSERVABILITY VIEW (Cloud Agnostic: OTel Gateway + Observe Inc + Obstack)
    # =========================================================================
    p4 = []
    p4.append(node("p4_title", "Cloud-Agnostic Enterprise AI Observability Architecture (OTel Gateway + Observe Inc + Obstack)", 150, 10, 1300, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    # Lane 1: Telemetry Collection & Dual-Tier OTel Gateway
    p4.append(lane("p4_l1", "1. Multi-Cloud Telemetry Ingestion & Dual-Tier OTel Gateway (AWS / Azure / GCP / Hybrid)", 30, 55, 1540, 115, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p4.append(node("p4_tier1_agent", "Tier 1: Cloud Local OTel Agents\n• AWS ADOT / Azure Monitor OTel\n• GCP OTel / On-Prem DaemonSets\n• Auto Resource Detection", 20, 34, 250, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p4_l1"))
    p4.append(node("p4_otel_gw", "Tier 2: Central OTel Gateway Cluster\n• Memory Limiter & Batching\n• In-VPC PII Regex Scrubbing\n• Tail-Based Trace Sampling (100% Errors)", 290, 34, 300, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p4_l1"))
    p4.append(node("p4_exporter_observe", "OTLP HTTP/gRPC Exporter\n(To Observe Inc. for Unified Logs & Tracing)", 610, 34, 280, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p4_l1"))
    p4.append(node("p4_exporter_obstack", "Prometheus Remote-Write Exporter\n(To Obstack / Prometheus for Metrics)", 910, 34, 280, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p4_l1"))
    p4.append(node("p4_cloud_native_exp", "Cloud-Native Compliance Fan-Out\n(AWS CloudWatch / Azure Mon / GCP Log)", 1210, 34, 310, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p4_l1"))

    # Lane 2: Telemetry Onboarding Across 4 Key Pillars
    p4.append(lane("p4_l2", "2. Unified Telemetry Onboarding: Customer Journey, Business, App/GenAI & Infrastructure Metrics", 30, 185, 1540, 135, "swimlane;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#64748b;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e293b;"))
    p4.append(node("p4_cust_journey", "① Customer Journey Telemetry\n• Onboarding & Login Funnel\n• Copilot Query -> RAG -> Action Flow\n• Session Drop-Off & CSAT Feedback\n• User Intent Completion Rate", 20, 36, 360, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p4_l2"))
    p4.append(node("p4_biz_metrics", "② Business & FinOps Metrics\n• Daily Active Copilot Users (DACU)\n• Tenant Query Volume & Tier Utilization\n• Token Spend vs Revenue Margin\n• Tool Invocation Value & Churn Risk", 400, 36, 360, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p4_l2"))
    p4.append(node("p4_app_genai", "③ Application & GenAI Telemetry\n• TTFT (<150ms P99 SLA) & TPOT\n• Semantic Cache Hit % (>40% target)\n• RAG Precision / Recall (Ragas / TruLens)\n• Model Fallback & Guardrail Intervention", 780, 36, 360, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p4_l2"))
    p4.append(node("p4_infra_metrics", "④ Infrastructure & Fleet Metrics\n• NVIDIA DCGM GPU VRAM / SM Util\n• Karpenter Provisioning Latency (<60s)\n• Spot Interruption & Eviction Rate\n• OTel Gateway Queue Depth & Drops", 1160, 36, 360, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p4_l2"))

    # Lane 3: Storage & Analytics Backends (Observe Inc. + Obstack)
    p4.append(lane("p4_l3", "3. Unified Storage, Dataset Modeling & TSDB Analytics Backends", 30, 335, 1540, 125, "swimlane;whiteSpace=wrap;html=1;fillColor=#f5f3ff;strokeColor=#8b5cf6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#5b21b6;"))
    p4.append(node("p4_observe_backend", "Observe Inc. Multi-Cloud Telemetry Hub\n• OPAL Dataset Modeling (Trace + Log Links)\n• Multi-Cloud Span Correlation (AWS <-> Azure <-> GCP)\n• Tenant-Scoped Log Exploration & Audit Queries", 20, 36, 560, 75, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p4_l3"))
    p4.append(node("p4_obstack_backend", "Obstack / Prometheus TSDB Metric Store\n• High-Cardinality Real-time Metric Storage\n• Pre-Aggregated Recording Rules for SLOs\n• Prometheus Alertmanager & Escalation Policies", 600, 36, 560, 75, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p4_l3"))
    p4.append(node("p4_ml_eval_backend", "Continuous AI Quality Evaluator\n• Automated Ragas & TruLens Scoring\n• Semantic Drift & Hallucination Flagging", 1180, 36, 340, 75, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p4_l3"))

    # Lane 4: Executive Single-Pane-of-Glass Dashboards & Alerting
    p4.append(lane("p4_l4", "4. Single-Pane-of-Glass Visualization, Multi-Tenant FinOps & SLA Alerting", 30, 475, 1540, 110, "swimlane;whiteSpace=wrap;html=1;fillColor=#ecfdf5;strokeColor=#10b981;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#065f46;"))
    p4.append(node("p4_dash_journey", "Grafana Journey & Biz Dashboard\n• User Funnel Drop-off Rate\n• DACU & Tenant Token Quota Burndown", 20, 36, 360, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p4_l4"))
    p4.append(node("p4_dash_slo", "Grafana AI SLA & Latency Dashboard\n• P99 TTFT (<150ms) & TPOT Trends\n• Regional Hub Availability (99.95% Target)", 400, 36, 360, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p4_l4"))
    p4.append(node("p4_dash_gpu", "Obstack GPU Fleet Health Dashboard\n• DCGM GPU Util, Temperature & NVLink\n• 60% Spot Utilization & Karpenter Scaling", 780, 36, 360, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p4_l4"))
    p4.append(node("p4_pager_ops", "PagerDuty & AI Incident Response\n• Instant P99 SLA Breach Alerts\n• Automatic Fallback & Runbook Automation", 1160, 36, 360, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p4_l4"))

    # Connectors for Page 4
    p4.append(edge("e4_1", "p4_tier1_agent", "p4_otel_gw", "OTLP gRPC (Local)"))
    p4.append(edge("e4_2", "p4_otel_gw", "p4_exporter_observe", "OTLP HTTP Logs & Spans"))
    p4.append(edge("e4_3", "p4_otel_gw", "p4_exporter_obstack", "Prometheus Remote Write"))
    p4.append(edge("e4_4", "p4_exporter_observe", "p4_observe_backend", "Ingest Logs/Traces"))
    p4.append(edge("e4_5", "p4_exporter_obstack", "p4_obstack_backend", "Ingest TSDB Metrics"))
    p4.append(edge("e4_6", "p4_observe_backend", "p4_dash_journey", "OPAL Dataset Queries"))
    p4.append(edge("e4_7", "p4_obstack_backend", "p4_dash_slo", "PromQL Real-Time Alerts"))

    diagrams.append(('ObservabilityView', '4. Observability & Monitoring', p4))

    # =========================================================================
    # 5. MLOPS / LLMOPS CI/CD PIPELINE VIEW
    # =========================================================================
    p5 = []
    p5.append(node("p5_title", "MLOps & LLMOps Automated Continuous Delivery Pipeline", 250, 10, 1100, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    p5.append(lane("p5_l1", "Stage 1: Continuous Integration, Testing & Security Verification (GitHub Actions / GitLab CI)", 30, 55, 1540, 110, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p5.append(node("p5_git", "Git Push / Pull Request\n(Prompt, LoRA, Agent Code)", 20, 36, 200, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p5_l1"))
    p5.append(node("p5_lint", "Code Linting & Unit Tests\n(Ruff, PyTest, TypeCheck)", 240, 36, 200, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p5_l1"))
    p5.append(node("p5_sec_scan", "Security & Vulnerability Scan\n(Trivy, SonarQube, Snyk, Gitleaks)", 460, 36, 230, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p5_l1"))
    p5.append(node("p5_prompt_eval", "Automated Prompt Benchmark\n(Golden Dataset vs LLM Evals)", 710, 36, 230, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p5_l1"))
    p5.append(node("p5_docker_build", "Container Build & Sign\n(Kaniko & Cosign Sigstore -> ECR)", 960, 36, 230, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p5_l1"))
    p5.append(node("p5_ecr", "Amazon ECR Multi-Region\n(Immutable Image Replication)", 1210, 32, 220, 62, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p5_l1"))

    p5.append(lane("p5_l2", "Stage 2: LoRA Fine-Tuning & Model Evaluation Benchmark (Spot Trainium / H100)", 30, 185, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#b45309;"))
    p5.append(node("p5_data_prep", "Domain Data Prep & Tokenization\n(S3 Tables Data Pipeline)", 20, 36, 230, 65, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p5_l2"))
    p5.append(node("p5_lora_train", "LoRA Fine-Tuning Job\n(AWS Trainium / H100 60% Spot Pool)", 270, 36, 240, 65, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p5_l2"))
    p5.append(node("p5_model_bench", "Automated Safety & Quality Bench\n(MT-Bench, Ragas Faithfulness > 0.90)", 530, 36, 260, 65, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p5_l2"))
    p5.append(node("p5_model_registry", "MLflow / Bedrock Model Registry\n(Versioned Weights, Metadata, Artifacts)", 810, 32, 260, 72, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p5_l2"))
    p5.append(node("p5_stage_gate", "Automated / HITL Approval Gate\n(Risk Assessment & Accuracy Check)", 1090, 36, 250, 65, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p5_l2"))

    p5.append(lane("p5_l3", "Stage 3: GitOps Multi-Region Progressive Deployment (ArgoCD & Flagger)", 30, 325, 1540, 110, "swimlane;whiteSpace=wrap;html=1;fillColor=#ecfdf5;strokeColor=#10b981;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#065f46;"))
    p5.append(node("p5_argocd", "ArgoCD Global GitOps Controller\n(Declarative K8s Manifest Sync)", 20, 36, 250, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p5_l3"))
    p5.append(node("p5_canary", "Flagger Progressive Canary Rollout\n(10% -> 25% -> 50% -> 100% Traffic)", 290, 36, 260, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p5_l3"))
    p5.append(node("p5_auto_rollback", "Automated Rollback Trigger\n(Rollback if Latency >150ms or Error >0.1%)", 570, 36, 270, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p5_l3"))
    p5.append(node("p5_5reg_deploy", "5 Regional EKS Hub Deployments\n(Sync to US-East, EU, APAC Hubs)", 860, 36, 260, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p5_l3"))
    p5.append(node("p5_warm_prep", "Warm Pool Pre-warming Action\n(Pre-load GPU weights into VRAM)", 1140, 36, 270, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p5_l3"))

    diagrams.append(('CicdView', '5. MLOps CI-CD Pipelines', p5))

    # =========================================================================
    # 6. DATA LINEAGE & PRIVACY GOVERNANCE VIEW
    # =========================================================================
    p6 = []
    p6.append(node("p6_title", "Enterprise Data Lineage, Privacy Governance & Tenant Isolation Architecture", 200, 10, 1200, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    p6.append(lane("p6_l1", "1. Multi-Tenant Ingestion & Automated PII Sanitization Flow", 30, 55, 1540, 110, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p6.append(node("p6_raw_doc", "Enterprise Raw Documents\n(PDF, Word, Confluence, DB)", 20, 36, 220, 55, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p6_l1"))
    p6.append(node("p6_parser", "Document Chunking & Parser\n(Preserve Semantic Hierarchy)", 260, 36, 220, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p6_l1"))
    p6.append(node("p6_pii_mask", "Presidio & AWS Macie PII Redaction\n(Hash / Anonymize PII Tokens)", 500, 36, 240, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p6_l1"))
    p6.append(node("p6_meta_tag", "Tenant Metadata & ACL Tagging\n(tenant_id, department, access_level)", 760, 36, 250, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p6_l1"))
    p6.append(node("p6_embed_gen", "Inf2 Embedding Model Fleet\n(Titan v2 / BGE-M3 1024-dim)", 1030, 36, 240, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p6_l1"))
    p6.append(node("p6_os_write", "OpenSearch Vector Index\n(Tenant-Keyed Partition)", 1290, 32, 220, 62, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p6_l1"))

    p6.append(lane("p6_l2", "2. Data Lineage Tracking, Vector Provenance & Audit Registry", 30, 185, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#f5f3ff;strokeColor=#8b5cf6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#5b21b6;"))
    p6.append(node("p6_lineage_engine", "AWS DataZone / OpenLineage\n• Track Origin Doc -> Chunks -> Vectors\n• Track Inference Prompts -> RAG Context", 20, 36, 320, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p6_l2"))
    p6.append(node("p6_vector_provenance", "Vector Provenance Metadata Store\n(Chunk ID, Timestamp, Source SHA-256)", 360, 32, 290, 72, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p6_l2"))
    p6.append(node("p6_inference_audit", "Inference Audit & Attribution Record\n(Prompt Hash, Used Context IDs, Output)", 670, 32, 290, 72, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p6_l2"))
    p6.append(node("p6_gdpr_purge", "Automated GDPR / 'Right to be Forgotten'\n(Purge by tenant_id or user_id across S3/Vectors)", 980, 36, 320, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p6_l2"))

    p6.append(lane("p6_l3", "3. Sovereign Boundary & Data Residency Enforcement (EU, US, APAC)", 30, 325, 1540, 110, "swimlane;whiteSpace=wrap;html=1;fillColor=#ecfdf5;strokeColor=#10b981;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#065f46;"))
    p6.append(node("p6_eu_bound", "EU Data Residency Boundary (eu-west-1)\n• Zero Data Egress outside EU\n• Sovereign EU KMS Key Wrapping", 20, 36, 360, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p6_l3"))
    p6.append(node("p6_us_bound", "US Data Residency Boundary (us-east-1)\n• FedRAMP / HIPAA Compliant Storage\n• Dedicated US Encryption HSM", 400, 36, 360, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p6_l3"))
    p6.append(node("p6_apac_bound", "APAC Data Residency Hub (Singapore/Tokyo)\n• Strict Regional Vector Storage\n• Local Model Execution Only", 780, 36, 360, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p6_l3"))
    p6.append(node("p6_compliance_report", "Automated Compliance Auditor\n(Real-Time GDPR / SOC2 Compliance Report)", 1160, 36, 260, 58, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p6_l3"))

    diagrams.append(('DataPrivacyView', '6. Data Privacy & Governance', p6))

    # =========================================================================
    # 7. RESILIENCE, HIGH AVAILABILITY & LLM FALLBACK VIEW
    # =========================================================================
    p7 = []
    p7.append(node("p7_title", "Operational Resilience, High Availability & Multi-Provider LLM Fallback Routing", 200, 10, 1200, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    p7.append(lane("p7_l1", "1. Multi-Region Active-Active Traffic Routing & Regional Failover", 30, 55, 1540, 110, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p7.append(node("p7_health_check", "Route 53 Global Health Checks\n(Continuous Probing of 5 Regional Hubs)", 20, 36, 260, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p7_l1"))
    p7.append(node("p7_failover_rule", "Automated Anycast Failover\n(Reroute Regional Traffic in <15 secs)", 300, 36, 260, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p7_l1"))
    p7.append(node("p7_surge_buffer", "SQS / Kinesis Surge Queues\n(Buffer 3x Seasonal Traffic Spikes)", 580, 36, 260, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p7_l1"))
    p7.append(node("p7_warm_pool_mgr", "Warm Pool Autoscaling Manager\n(Maintain 20% Hot Spares in Memory)", 860, 36, 270, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p7_l1"))
    p7.append(node("p7_chaos_eng", "AWS Fault Injection Simulator\n(Automated Regional Chaos Experiments)", 1150, 36, 270, 55, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p7_l1"))

    p7.append(lane("p7_l2", "2. Multi-Provider LLM Fallback & Circuit Breaker Cascading Engine", 30, 185, 1540, 140, "swimlane;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#f59e0b;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#b45309;"))
    p7.append(node("p7_cb_router", "Circuit Breaker & Resilience Router\n• Tracks Error Rate & P99 Latency\n• Triggers Graceful Degradation", 20, 36, 260, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p7_l2"))
    p7.append(node("p7_pri_llm", "Tier 1: Local vLLM Inference (Primary)\n• L4 / Graviton GPU Cluster\n• SLA Target: Sub-150ms Latency\n• Status: Active (Primary)", 300, 36, 260, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p7_l2"))
    p7.append(node("p7_sec_llm", "Tier 2: Amazon Bedrock (Secondary)\n• Managed Claude 3.5 Sonnet / Haiku\n• Automatic API Retry with Backoff\n• Status: Standby Fallback", 580, 36, 270, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p7_l2"))
    p7.append(node("p7_ter_llm", "Tier 3: Multi-Cloud / Self-Hosted SLM\n• Quantized Llama-3 8B (CPU/Graviton)\n• Emergency Graceful Offline Mode\n• Status: Disaster Recovery", 870, 36, 280, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p7_l2"))
    p7.append(node("p7_status_page", "System Status & SLA Dashboard\n• Real-Time Circuit Status\n• Multi-Region Uptime (99.95% Target)", 1170, 36, 250, 85, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p7_l2"))

    diagrams.append(('ResilienceView', '7. HA & Multi-Provider Fallback', p7))

    # =========================================================================
    # 8. MULTI-AGENT ORCHESTRATION & TOOL EXECUTION VIEW
    # =========================================================================
    p8 = []
    p8.append(node("p8_title", "Bedrock AgentCore Multi-Agent Orchestration & Tool Execution Architecture", 200, 10, 1200, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    p8.append(lane("p8_l1", "1. Supervisor Agent & Goal Decomposition Runtime", 30, 55, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#f5f3ff;strokeColor=#8b5cf6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#5b21b6;"))
    p8.append(node("p8_user_intent", "User Copilot Request\n(Complex Multi-Step Task)", 20, 36, 220, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p8_l1"))
    p8.append(node("p8_supervisor", "Bedrock AgentCore Supervisor\n• Intent Parsing & Task Decomposition\n• DAG Execution Planner & State Machine", 260, 36, 300, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p8_l1"))
    p8.append(node("p8_shared_state", "Shared Agent State & Short-Term Memory\n(DynamoDB Global Table + Redis)", 580, 32, 290, 72, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p8_l1"))
    p8.append(node("p8_long_memory", "Long-Term Vector Memory (OpenSearch)\n(User Preferences, Past Interactions)", 890, 32, 290, 72, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p8_l1"))
    p8.append(node("p8_eval_critique", "Agent Self-Reflection & Critique Loop\n(Evaluate Tool Output Quality)", 1200, 36, 230, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p8_l1"))

    p8.append(lane("p8_l2", "2. Specialized Worker Agents & Tool Sandboxes", 30, 195, 1540, 130, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p8.append(node("p8_rag_worker", "Worker 1: Enterprise RAG Agent\n• Semantic Vector Search\n• BM25 Keyword Hybrid Search\n• Context Reranking (Cohere)", 20, 36, 260, 78, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p8_l2"))
    p8.append(node("p8_api_worker", "Worker 2: SaaS Integration Agent\n• OpenAPI Tool Registry\n• Salesforce, Jira, HubSpot Connectors\n• Tenant Token Forwarding", 300, 36, 260, 78, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p8_l2"))
    p8.append(node("p8_code_worker", "Worker 3: Code & Analytics Agent\n• Generates SQL / Python / Bash\n• Data Aggregation & Charting\n• Sandboxed Execution", 580, 36, 260, 78, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p8_l2"))
    p8.append(node("p8_sandbox_exec", "Firecracker MicroVM / WASM Sandbox\n• Isolated Ephemeral Execution\n• 500ms Max Runtime Quota\n• Strict Network Isolation", 860, 36, 280, 78, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p8_l2"))
    p8.append(node("p8_aggregator", "Response Synthesizer & Streamer\n• Merge Multi-Agent Results\n• Stream Server-Sent Events (SSE)", 1160, 36, 260, 78, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p8_l2"))

    diagrams.append(('MultiAgentView', '8. Multi-Agent Orchestration', p8))

    # =========================================================================
    # 9. FINOPS & SEMANTIC CACHE COST OPTIMIZATION VIEW
    # =========================================================================
    p9 = []
    p9.append(node("p9_title", "FinOps & GPU Cost Optimization Architecture (~60% Spot & Semantic Cache)", 200, 10, 1200, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    p9.append(lane("p9_l1", "1. Semantic Caching & Model Cascading Routing (~40% Token Cost Reduction)", 30, 55, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#b45309;"))
    p9.append(node("p9_raw_query", "Incoming Copilot Query\n(User Request + Session)", 20, 36, 200, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p9_l1"))
    p9.append(node("p9_redis_cache", "ElastiCache Redis Semantic Cache\n• Embed query via Fast Embedding\n• Cosine Sim >= 0.95 -> Direct Hit\n• Latency: <15ms ($0 LLM Cost)", 240, 32, 270, 75, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p9_l1"))
    p9.append(node("p9_router_classify", "Query Complexity Classifier (Lightweight)\n• Intent: Simple Q&A vs Complex DAG\n• Token Estimation & Budget Check", 530, 36, 280, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#f59e0b;fontStyle=1;fontSize=10;shadow=1;", "p9_l1"))
    p9.append(node("p9_slm_tier", "Tier 1: Small SLM (Llama-3 8B on Graviton)\n• 70% of standard user queries\n• 10x Cheaper per 1k Tokens", 830, 36, 290, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p9_l1"))
    p9.append(node("p9_llm_tier", "Tier 2: Frontier LLM (Claude 3.5 Sonnet)\n• 30% complex multi-step reasoning\n• High precision output", 1140, 36, 280, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p9_l1"))

    p9.append(lane("p9_l2", "2. Spot Compute Orchestration & Warm Pool Autoscaling (~60% Compute Cost Reduction)", 30, 195, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#3b82f6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#1e40af;"))
    p9.append(node("p9_spot_train", "Trainium / H100 60% Spot Pool\n• Asynchronous Fine-Tuning & Batch\n• Automated Spot Interruption Checkpointing\n• Saves up to 70% vs On-Demand", 20, 36, 320, 72, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p9_l2"))
    p9.append(node("p9_karp_binpack", "Karpenter Bin-Packing Engine\n• Consolidates fragmented GPU pods\n• Scales down idle instances in <60s\n• Mixed Instance Policy (L4, A10G, Inf2)", 360, 36, 310, 72, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p9_l2"))
    p9.append(node("p9_warm_pool_cost", "Warm Pool Dynamic Resizing\n• Schedules warm nodes based on history\n• Pre-empts seasonal 3x surges\n• Zero Idle GPU waste", 690, 36, 300, 72, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p9_l2"))
    p9.append(node("p9_kubecost", "Kubecost & AWS Cost Explorer\n• Real-Time Tenant GPU Cost Allocation\n• Automated Quota Throttling & Alerts\n• Monthly Executive FinOps Reports", 1010, 36, 320, 72, "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#3b82f6;fontStyle=1;fontSize=10;shadow=1;", "p9_l2"))

    diagrams.append(('FinOpsView', '9. FinOps & Semantic Cache', p9))

    # =========================================================================
    # 10. AI MODEL GOVERNANCE, SAFETY & HITL EVALUATION VIEW
    # =========================================================================
    p10 = []
    p10.append(node("p10_title", "AI Model Governance, Safety Guardrails & Human-In-The-Loop (HITL) Architecture", 180, 10, 1240, 35, "text;html=1;fontSize=20;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#0f172a;"))

    p10.append(lane("p10_l1", "1. Real-time Output Evaluation & Confidence Gating Engine", 30, 55, 1540, 120, "swimlane;whiteSpace=wrap;html=1;fillColor=#fef2f2;strokeColor=#ef4444;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#991b1b;"))
    p10.append(node("p10_gen_output", "Generated AI Response\n(Draft Output + Citations)", 20, 36, 210, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p10_l1"))
    p10.append(node("p10_ragas_score", "Ragas Faithfulness & Relevance Scorer\n• Evaluates grounding against retrieved docs\n• Confidence Threshold >= 0.85", 250, 36, 300, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p10_l1"))
    p10.append(node("p10_safety_check", "Safety & Toxicity Filter (NeMo)\n• Check for bias, toxic tone, hallucinations\n• Verify zero PII in output", 570, 36, 290, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p10_l1"))
    p10.append(node("p10_decision_gate", "Automated Gate Decision\n• High Confidence (>0.85) -> Auto-Approve\n• Low Confidence (<0.85) -> HITL Escalate", 880, 36, 290, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fee2e2;strokeColor=#ef4444;fontStyle=1;fontSize=10;shadow=1;", "p10_l1"))
    p10.append(node("p10_direct_stream", "Direct Stream to User\n(SSE Stream Sub-150ms)", 1190, 36, 220, 68, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p10_l1"))

    p10.append(lane("p10_l2", "2. Human-In-The-Loop (HITL) Review, Red-Teaming & Continuous Feedback Loop", 30, 195, 1540, 130, "swimlane;whiteSpace=wrap;html=1;fillColor=#f5f3ff;strokeColor=#8b5cf6;fontStyle=1;startSize=26;rounded=1;fontSize=11;fontColor=#5b21b6;"))
    p10.append(node("p10_hitl_queue", "Amazon A2I / HITL Review Queue\n(Escalated Prompts with Context)", 20, 36, 260, 75, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p10_l2"))
    p10.append(node("p10_domain_reviewer", "Enterprise Domain Expert Reviewer\n• Human approves / edits answer\n• Annotates failure reason & feedback", 300, 36, 280, 75, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p10_l2"))
    p10.append(node("p10_feedback_db", "RLHF / DPO Preference Dataset Store\n(Curated Gold Standard Responses in S3)", 600, 32, 290, 80, "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p10_l2"))
    p10.append(node("p10_red_team", "Automated AI Red-Teaming Suite\n(Adversarial attack probes & prompt injections)", 910, 36, 290, 75, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#8b5cf6;fontStyle=1;fontSize=10;shadow=1;", "p10_l2"))
    p10.append(node("p10_model_retrain", "Continuous LoRA Retraining Trigger\n(Monthly fine-tune with verified feedback)", 1220, 36, 230, 75, "rounded=1;whiteSpace=wrap;html=1;fillColor=#d1fae5;strokeColor=#10b981;fontStyle=1;fontSize=10;shadow=1;", "p10_l2"))

    diagrams.append(('GovernanceHITLView', '10. AI Safety & HITL Review', p10))

    # =========================================================================
    # ASSEMBLE FULL XML FILE
    # =========================================================================
    xml_lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<mxfile host="Electron" modified="2026-09-06T18:40:00.000Z" agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) draw.io/24.0.0 Chrome/120.0.0.0 Electron/29.0.0 Safari/537.36" version="24.0.0" type="device">'
    ]

    for diag_id, diag_name, cells in diagrams:
        xml_lines.append(f'  <diagram id="{diag_id}" name="{esc(diag_name)}">')
        xml_lines.append('    <mxGraphModel dx="1600" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1200" math="0" shadow="0">')
        xml_lines.append('      <root>')
        xml_lines.append('        <mxCell id="0" />')
        xml_lines.append('        <mxCell id="1" parent="0" />')
        for c in cells:
            for line in c.split('\n'):
                xml_lines.append(f'        {line}')
        xml_lines.append('      </root>')
        xml_lines.append('    </mxGraphModel>')
        xml_lines.append('  </diagram>')

    xml_lines.append('</mxfile>')

    return '\n'.join(xml_lines)

if __name__ == '__main__':
    content = create_drawio_xml()
    out_path = 'lab-ai-system-designs/saas-ai-platform/multi_region_saas_ai_platform.drawio'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully generated {out_path} with {len(content)} bytes")
