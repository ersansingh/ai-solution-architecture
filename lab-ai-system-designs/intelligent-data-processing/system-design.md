# Enterprise AI System Design: Intelligent Document Processing (IDP) for Insurance Claims

> **Skill**: `ai-system-design-architect`  
> **Input**: [`algorithm-recommendation.md`](algorithm-recommendation.md) · [`Session2_IDP_Problem_Statement.pdf`](Session2_IDP_Problem_Statement.pdf)  
> **Date**: 2026-10-11  
> **Architecture Version**: v1.0

---

## 1. AI Problem Classification

| Attribute | Detail |
| :--- | :--- |
| **Domain** | Document Intelligence + Multi-Modal AI |
| **Sub-Domains** | OCR / Form Parsing · Information Extraction (NER) · Document Classification · Semantic Validation · Workflow Automation |
| **Input Modalities** | Images (JPEG/PNG/TIFF scanned docs), PDF (native + scanned), Email bodies (text), Mobile captures |
| **Output Types** | Structured JSON extraction · Validated claim record · Routing decision · Audit trail |
| **Scale** | Thousands of claims/day → 500K–2M documents/year |
| **Latency Class** | Real-time (<3s per document, API-driven) + Batch (overnight bulk, >1000 docs/hour) |
| **Compliance** | Insurance sector data governance, GDPR/CCPA, PII handling, audit trail requirement |

---

## 2. Architecture Pattern Selection

### Selected Pattern: **Hybrid — Document AI + RAG + Predictive ML**

```
Multi-Channel Ingestion
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  PIPELINE 1: Document AI (Transfer Learning)             │
│  LayoutLMv3 → Document Classification + NER/Extraction  │
└──────────────────────────────────────────────────────────┘
        │ Structured Extracted Fields
        ▼
┌──────────────────────────────────────────────────────────┐
│  PIPELINE 2: RAG Validation (Generative AI)              │
│  BGE-M3 + Llama-3-8B → Semantic Cross-Field Validation  │
└──────────────────────────────────────────────────────────┘
        │ Validated / Flagged Record
        ▼
┌──────────────────────────────────────────────────────────┐
│  PIPELINE 3: Predictive ML (Traditional ML)              │
│  XGBoost → Fraud Scoring + Anomaly Detection            │
└──────────────────────────────────────────────────────────┘
        │
        ▼
  Claims System Integration (REST API / Event Streaming)
```

**Rationale for Hybrid Pattern**:
- **Document AI** (LayoutLMv3): The primary complexity is multi-format, layout-aware extraction — no single pattern handles this. Transfer learning on document foundation models is the only production-grade approach.
- **RAG Validation**: Semantic insurance policy validation requires grounded reasoning against a knowledge base. RAG avoids costly fine-tuning while providing auditable, citation-backed outputs.
- **Predictive ML**: Fraud scoring on structured extracted fields is a classic tabular classification problem best served by XGBoost with SHAP explainability for compliance.

---

## 3. Architecture Reasoning

### Why This Component Set

| Decision | Reasoning |
| :--- | :--- |
| **LayoutLMv3 over pure LLM** | Layout-awareness is critical for form-based insurance documents. LayoutLMv3 jointly encodes text + visual layout; pure LLMs cannot process raw images without vision towers |
| **Triton Inference Server** | GPU-optimized serving for LayoutLMv3 ONNX models; batching support reduces per-document GPU cost; native Kubernetes autoscaling |
| **vLLM for Llama-3-8B** | PagedAttention for high-throughput LLM serving; self-hosted for PII compliance (no data leaves the VPC) |
| **Pinecone / pgvector** | Vector similarity search for RAG retrieval of insurance policy documents; pgvector for on-premise/compliance-constrained deployments |
| **Kafka for real-time ingestion** | Decouples ingestion channels (email, mobile, scan) from processing pipeline; enables backpressure handling during peak claim volumes |
| **Apache Airflow** | Orchestrates batch processing pipelines, retraining schedules, and model promotion workflows |
| **AWS as primary cloud** | S3 for document storage, SageMaker for training, EKS for inference, MSK for Kafka; mature ML ecosystem |
| **Azure AI as fallback** | Azure Document Intelligence (Form Recognizer) as PoC/fallback; Azure OpenAI for LLM redundancy |
| **Evidently AI** | Best-in-class ML monitoring for data drift, document quality drift, and extraction accuracy monitoring |
| **Presidio for PII** | Open-source Microsoft PII detection and anonymization — applies before any LLM processing |

---

## 4. AI System Context

| Attribute | Detail |
| :--- | :--- |
| **Business Problem** | Insurance claims processing taking days due to manual multi-format document handling |
| **AI Use Case** | Intelligent Document Processing — automate classification, extraction, validation, and routing |
| **Primary Users** | Claims Adjusters, Operations Teams (human review queue); API consumers (claims systems) |
| **Input** | Multi-channel documents: scanned PDFs, JPEG/TIFF images, email attachments, mobile photos |
| **Output** | Structured JSON claim records → validated → routed to claims system or human review queue |
| **Processing Scale** | Thousands documents/day; peak: burst capacity up to 10x normal volume |
| **Latency SLA** | Real-time channel: <3s end-to-end; Batch channel: >1000 docs/hour throughput |
| **Accuracy Target** | >95% STP (Straight-Through Processing) rate; <5% human review escalation |
| **Primary Cloud** | AWS (EKS, S3, MSK, SageMaker, CloudWatch) |
| **Secondary / Fallback** | Azure (Azure AI Document Intelligence, Azure OpenAI) |
| **Compliance** | Insurance sector data governance, PII masking before LLM, audit log for every document |

---

## 5. Architecture Components (8 Enterprise Layers)

### Layer 1: User Layer
| Component | Role |
| :--- | :--- |
| 📱 Mobile App Upload Portal | Mobile capture and upload of claim-related photos and documents |
| 📧 Email Ingestion Gateway | Parses email attachments from claimants, brokers, and medical providers |
| 🖥️ Claims Adjuster Web Console | Human review queue interface for low-confidence and flagged documents |
| 🔌 Partner API Clients | B2B integrations with insurance brokers, hospitals, and legal firms |
| 📠 Physical Scan Station | Scanner endpoint that pushes TIFF/PDF to the ingestion bus |

### Layer 2: Application Layer
| Component | Role |
| :--- | :--- |
| 🌐 API Gateway (Kong) | Single entry point for all REST API consumers; rate limiting, auth |
| ⚖️ Application Load Balancer (ALB) | Distributes traffic across IDP microservices; health-check routing |
| 🔄 Document Ingestion Orchestrator | Routes documents by channel type and format to correct processing pipeline |
| 📋 Human Review Console (FastAPI + React) | Web UI for adjuster review, field correction, and manual override |
| 📬 Notification Service | Sends processing status webhooks and email notifications |

### Layer 3: API / Integration Layer
| Component | Role |
| :--- | :--- |
| 📡 IDP REST API (FastAPI) | `/classify`, `/extract`, `/validate`, `/status` endpoints |
| 🔐 OAuth2 / OIDC Auth Server (Keycloak) | Token issuance and validation for all API consumers |
| 🔗 Claims System Integration API | Bidirectional REST/gRPC integration with downstream claims management systems |
| 📊 Webhook Delivery Service | Event-driven notifications to partner systems on completion |

### Layer 4: AI / ML Layer
| Component | Technology | Role |
| :--- | :--- | :--- |
| 🖼️ Image Preprocessing Service | OpenCV + ESRGAN | Deskewing, denoising, super-resolution for low-quality scans |
| 🔤 OCR Engine | Tesseract 5 + PaddleOCR | Text extraction with bounding box coordinates |
| 📄 Document Classifier | LayoutLMv3 (fine-tuned) | Multi-class document type classification |
| 🏷️ Field Extractor (NER) | LayoutLMv3 Token Classification | BIO-tagged named entity extraction with spatial coordinates |
| 🧠 RAG Validation Engine | LangChain + BGE-M3 + Llama-3-8B | Semantic cross-field consistency validation against policy KB |
| 🎯 Fraud Scorer | XGBoost + SHAP | Tabular fraud probability scoring on extracted fields |
| 🔍 Anomaly Detector | Isolation Forest | Unsupervised anomaly detection on document embeddings |
| 📚 Vector Search (Policy KB) | Pinecone / pgvector | Semantic retrieval of insurance policy rules and guidelines |
| 🔒 PII Detection & Masking | Microsoft Presidio | Auto-detect and mask PII before LLM processing |
| 🤖 LLM Serving | vLLM (Llama-3-8B-Instruct) | High-throughput LLM inference for validation reasoning |
| ⚡ Model Serving | Triton Inference Server | GPU-optimized LayoutLMv3 inference with ONNX export |
| 📦 Feature Store | Databricks Feature Store | Structured extracted fields for fraud/analytics downstream use |

### Layer 5: Data Layer
| Component | Technology | Role |
| :--- | :--- | :--- |
| 📥 Document Ingestion Bus | Apache Kafka (AWS MSK) | Async multi-channel ingestion; decouples producers/consumers |
| 🗄️ Raw Document Store | AWS S3 (Bronze Zone) | Immutable raw document archive |
| 🗄️ Processed Document Store | AWS S3 (Silver Zone) | OCR output, bounding boxes, preprocessing artifacts |
| 🗄️ Validated Records Store | AWS S3 + PostgreSQL (Gold Zone) | Validated structured claim records |
| 🗃️ Metadata Database | PostgreSQL (RDS) | Document metadata, processing status, audit entries |
| 📊 Extraction Results DB | Amazon DynamoDB | High-throughput read/write for extraction results and routing decisions |
| 📚 Policy Knowledge Base | Pinecone / pgvector (PostgreSQL) | Vector embeddings of insurance policy documents |
| 🔄 Stream Processing | Apache Kafka Streams | Real-time document routing, status updates, error handling |
| 📋 Batch Processing | Apache Airflow (MWAA) | Orchestrates batch reprocessing, retraining, and model promotion |

### Layer 6: Security Layer
| Component | Role |
| :--- | :--- |
| 🛡️ WAF (AWS WAF) | API endpoint protection against injection and DDoS |
| 🔐 Identity & Access (Keycloak / AWS Cognito) | OAuth2/OIDC for all human users and service accounts |
| 🔑 Secret Management (AWS Secrets Manager) | Rotation of API keys, DB credentials, model API tokens |
| 🔒 KMS Encryption | AES-256 encryption at rest for S3, RDS, DynamoDB |
| 🔒 TLS 1.3 | All in-transit data encryption between services |
| 🕵️ PII Detector (Presidio) | Auto-identify and mask PII fields before LLM processing and logging |
| 📋 Audit Logger | Immutable audit trail: every document, every model decision, every field change |
| 🛡️ AI Guardrails (NeMo Guardrails) | Prompt injection defense and output safety filtering for LLM layer |
| 🔐 mTLS (Service Mesh - Istio) | Mutual TLS between all microservices within the Kubernetes cluster |
| 🔍 RBAC | Role-based access: Claims Adjuster, Supervisor, Admin, System roles |

### Layer 7: Infrastructure Layer
| Component | Technology |
| :--- | :--- |
| 🖥️ Container Orchestration | AWS EKS (Kubernetes 1.29) |
| ⚡ GPU Inference Nodes | g4dn.2xlarge (NVIDIA T4) — Triton + vLLM serving |
| 🖥️ CPU Worker Nodes | m6i.4xlarge — Preprocessing, OCR, Airflow, API services |
| 🌐 VPC / Networking | VPC 10.0.0.0/16; Public subnets (ALB/NAT); Private subnets (EKS); Database subnets (RDS/DynamoDB) |
| 🔗 Service Mesh | Istio (mTLS, traffic management, observability) |
| 📡 Message Broker | AWS MSK (Managed Kafka) 3-broker cluster |
| 🗄️ Object Storage | AWS S3 with versioning, lifecycle policies, intelligent tiering |
| 🗄️ Relational DB | AWS RDS PostgreSQL Multi-AZ |
| 🚀 Auto-Scaling | HPA for API pods; Karpenter for GPU node provisioning |
| 🌍 CDN | AWS CloudFront for static assets and API caching |

### Layer 8: Operations & Observability Layer
| Component | Technology | Role |
| :--- | :--- | :--- |
| 📊 Metrics | Prometheus + Grafana | API latency, throughput, GPU utilization, OCR confidence, model accuracy |
| 📝 Logging | AWS CloudWatch + Elasticsearch (ELK) | Centralized log aggregation, search, and retention |
| 🔍 Distributed Tracing | Jaeger + OpenTelemetry | End-to-end trace: API → OCR → LayoutLMv3 → RAG → Kafka |
| 🤖 ML Monitoring | Evidently AI | Data drift (PSI), extraction accuracy, document quality distribution shift |
| 🚨 Alerting | PagerDuty + Grafana Alerts | STP rate drop below 93%, latency spike, model accuracy degradation |
| 🔄 Experiment Tracking | MLflow | Fine-tuning runs, validation curves, model version history |
| 📋 Model Registry | MLflow Model Registry | Experimental → Staging → Candidate → Production gates |
| 🧪 Chaos Engineering | AWS Fault Injection Simulator | Quarterly resilience testing |

---

## 6. Interaction Flow (Step-by-Step)

```
Step 1:  Document arrives via multi-channel intake
         └─ Email attachment → Email Gateway → Kafka topic: raw.documents
         └─ Mobile upload → API Gateway → Kong → Kafka topic: raw.documents
         └─ Scanner → TIFF upload → S3 Bronze → Kafka trigger
         └─ Partner API → REST /ingest → Kafka topic: raw.documents

Step 2:  Document Preprocessor (OpenCV + ESRGAN) consumes from Kafka
         └─ Deskew, denoise, super-resolution to 300 DPI
         └─ Format normalization: TIFF/JPEG/PNG → PDF → S3 Silver
         └─ Image quality score computed → low quality flag if < threshold

Step 3:  OCR Engine (Tesseract 5 + PaddleOCR) processes normalized image
         └─ Extracts text tokens + bounding boxes (x0,y0,x1,y1 normalized [0,1000])
         └─ Confidence score per token
         └─ OCR output → S3 Silver (JSON with tokens + coordinates)

Step 4:  PII Detection (Presidio) scans OCR output
         └─ Identifies: SSN, DOB, Driver License, Address, Names
         └─ Masks PII in working copy before LLM processing
         └─ Original with PII retained in encrypted S3 Bronze (compliance)

Step 5:  LayoutLMv3 Document Classifier consumes OCR tokens + bounding boxes
         └─ Classifies into: FNOL Form / Medical Record / Police Report /
            Police FIR / Repair Estimate / Bank Statement / Correspondence
         └─ Classification confidence score → if < 0.80: route to human queue

Step 6:  LayoutLMv3 NER Extractor extracts insurance fields
         └─ Extracts: Claimant Name, Policy Number, Date of Loss, Incident Type,
            Damage Amount, Vehicle Details, Witness Names, Medical Facility, etc.
         └─ BIO-tagged extraction with per-field confidence scores
         └─ Structured JSON → DynamoDB + S3 Silver

Step 7:  RAG Validation Engine performs semantic validation
         └─ BGE-M3 embeds extracted fields as query
         └─ Pinecone retrieves top-5 relevant policy rules
         └─ Llama-3-8B-Instruct validates: "Is claim_amount consistent with
            incident_type and policy_coverage?"
         └─ Validation result: PASS / FLAG (with reason + cited policy rule)

Step 8:  XGBoost Fraud Scorer evaluates structured extracted fields
         └─ Features: field completeness, cross-field consistency flags,
            historical claim frequency, damage amount vs. policy limit ratio
         └─ Fraud probability score (0.0–1.0) with SHAP feature attribution

Step 9:  Routing Decision Engine combines all signals
         └─ STP Route: All confidence > threshold + RAG PASS + Fraud score < 0.3
            → Auto-approve → Claims System Integration API
         └─ Human Review Route: Any low confidence OR RAG FLAG OR Fraud score > 0.3
            → Human Review Queue → Claims Adjuster Console

Step 10: Claims System Integration
         └─ Validated structured JSON → REST API → Core Claims Management System
         └─ Event published to Kafka topic: claims.processed
         └─ Webhook notification to partner system (if applicable)

Step 11: Audit Trail Recording
         └─ Every document: ingestion timestamp, model decisions, confidence scores,
            field extraction, validation result, fraud score, routing decision
         └─ Immutable audit log → PostgreSQL Audit Table + CloudWatch Logs Archive

Step 12: Monitoring & Feedback Loop
         └─ Evidently AI: monitor extraction F1, OCR quality drift, STP rate
         └─ Adjuster corrections in Human Review Console → Active Learning Queue
         └─ Airflow: monthly retraining pipeline triggered with new labeled data
         └─ MLflow: new model version evaluated → Staging → Canary (5%) → Production
```

---

## 7. Architecture Diagrams

### C4 Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Context                            │
│                                                                 │
│  [Claimants]  [Brokers]  [Medical Providers]  [Legal Firms]     │
│       │           │              │                  │           │
│       └───────────┴──────────────┴──────────────────┘           │
│                            │ Multi-channel                       │
│                            ▼                                    │
│         ┌─────────────────────────────────┐                     │
│         │   IDP AI PLATFORM (System)      │                     │
│         │                                 │                     │
│         │  Intelligent Document           │                     │
│         │  Processing for Insurance       │                     │
│         │  Claims                         │                     │
│         └─────────────────────────────────┘                     │
│                            │ Validated Records                  │
│                            ▼                                    │
│         [Core Claims System]  [Data Warehouse]  [Compliance]    │
└─────────────────────────────────────────────────────────────────┘
```

### C4 Container Diagram

```
┌──────────────────── IDP AI PLATFORM ──────────────────────────┐
│                                                                │
│  ┌──────────────┐    ┌───────────────┐    ┌────────────────┐  │
│  │  Ingestion   │    │  Processing   │    │  Validation    │  │
│  │  Gateway     │───▶│  Pipeline     │───▶│  Pipeline      │  │
│  │  (Kong+Kafka)│    │  (OCR+DL)     │    │  (RAG+XGBoost) │  │
│  └──────────────┘    └───────────────┘    └────────────────┘  │
│          │                   │                    │            │
│          ▼                   ▼                    ▼            │
│  ┌──────────────┐    ┌───────────────┐    ┌────────────────┐  │
│  │  S3 Document │    │  LayoutLMv3   │    │  Claims        │  │
│  │  Store       │    │  Model Serving│    │  Integration   │  │
│  │  (Bronze/    │    │  (Triton)     │    │  API           │  │
│  │   Silver/    │    └───────────────┘    └────────────────┘  │
│  │   Gold)      │    ┌───────────────┐    ┌────────────────┐  │
│  └──────────────┘    │  LLM Serving  │    │  Human Review  │  │
│                      │  (vLLM)       │    │  Queue         │  │
│                      └───────────────┘    └────────────────┘  │
│                                                                │
│  ─────── Cross-Cutting: Security · Observability · MLOps ────  │
└────────────────────────────────────────────────────────────────┘
```

### Logical Flow View (Text Representation)

```
[Users/Channels] → [API Gateway/Kong] → [Kafka MSK]
                                              │
                    ┌─────────────────────────┤
                    │                         │
                    ▼                         ▼
            [Preprocessing]           [Batch Orchestrator]
            [OpenCV+ESRGAN]           [Apache Airflow]
                    │
                    ▼
              [OCR Engine]
              [Tesseract+PaddleOCR]
                    │
                    ▼
              [PII Masking]
              [Presidio]
                    │
                    ├──────────────────────────┐
                    ▼                          ▼
          [Doc Classifier]           [Field Extractor]
          [LayoutLMv3 - Triton]     [LayoutLMv3 NER - Triton]
                    │                          │
                    └──────────┬───────────────┘
                               ▼
                    [RAG Validation Engine]
                    [BGE-M3 + Pinecone + vLLM]
                               │
                               ▼
                    [Fraud Scorer]
                    [XGBoost + SHAP]
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
           [Auto-Approve]          [Human Review Queue]
           [Claims API]            [Adjuster Console]
                    │
                    ▼
           [Core Claims System]
           [Audit Trail + Kafka]

           ─── Observability ───
           [Evidently AI] [Prometheus] [Grafana] [Jaeger]
```

---

## 8. Draw.io Architecture Diagram File

> The multi-page Draw.io architecture diagram is saved as:  
> **[`idp-insurance-architecture.drawio`](idp-insurance-architecture.drawio)**

Pages included (10-page enterprise architecture):
1. **Logical Architecture** — End-to-end component flow across 8 layers
2. **Infrastructure (Multi-Cloud)** — AWS primary + Azure fallback topology
3. **Infrastructure (Region Detail)** — AWS VPC/AZ/Subnet nested layout
4. **Data Architecture** — Document lake Bronze/Silver/Gold pipeline
5. **MLOps CI/CD Pipeline** — Training → Registry → Canary → Production
6. **Model Serving Architecture** — Triton + vLLM + KServe detail
7. **Security & Governance** — 4-quadrant IAM/Policy/Audit/Threat
8. **Monitoring & Operations** — 4-layer observability stack
9. **Data Lineage & Privacy Governance** — PII flow and lineage tracking
10. **AI Safety & HITL Review** — Model governance and human review gates

---

## 9. Infrastructure Architecture

### Network Topology

```
AWS Region: us-east-1
├── VPC: 10.0.0.0/16
│   ├── Public Subnets (10.0.1.0/24, 10.0.2.0/24) — AZ-a, AZ-b
│   │   ├── Application Load Balancer
│   │   ├── NAT Gateways
│   │   └── Internet Gateway
│   ├── Private Subnets (10.0.10.0/24, 10.0.11.0/24) — AZ-a, AZ-b
│   │   ├── EKS Node Groups (CPU: m6i.4xlarge)
│   │   ├── EKS GPU Node Group (GPU: g4dn.2xlarge)
│   │   ├── MSK Kafka Brokers
│   │   └── Airflow Workers
│   └── Database Subnets (10.0.20.0/24, 10.0.21.0/24) — AZ-a, AZ-b
│       ├── RDS PostgreSQL Multi-AZ (db.r6g.xlarge)
│       └── ElastiCache Redis (cache.r6g.large)
├── S3 Buckets (VPC Endpoint — no public routing)
│   ├── idp-raw-documents (Bronze)
│   ├── idp-processed-documents (Silver)
│   └── idp-validated-records (Gold)
└── CloudFront Distribution (Adjuster Web Console)

Azure (Fallback / DR):
├── Azure Document Intelligence (Form Recognizer) — PoC/fallback extraction
├── Azure OpenAI (GPT-4o-mini) — LLM fallback when vLLM unavailable
└── Azure Blob Storage — Cross-cloud document backup (GRS)
```

### Kubernetes Workloads

| Deployment | Replicas | Node Type | Resources |
| :--- | :--- | :--- | :--- |
| `idp-api` (FastAPI) | 3-10 (HPA) | m6i.4xlarge | 2 CPU, 4GB RAM |
| `preprocessing-worker` | 5-20 (HPA) | m6i.4xlarge | 4 CPU, 8GB RAM |
| `ocr-worker` | 5-20 (HPA) | m6i.4xlarge | 4 CPU, 8GB RAM |
| `triton-server` (LayoutLMv3) | 2-6 (HPA) | g4dn.2xlarge | 8 CPU, 32GB RAM, 1 T4 GPU |
| `vllm-server` (Llama-3-8B) | 2-4 (HPA) | g4dn.2xlarge | 8 CPU, 32GB RAM, 1 T4 GPU |
| `fraud-scorer` (XGBoost) | 3-8 (HPA) | m6i.4xlarge | 2 CPU, 4GB RAM |
| `airflow-scheduler` | 1 | m6i.2xlarge | 4 CPU, 8GB RAM |
| `kafka-consumer-group` | 10 (manual) | m6i.4xlarge | 4 CPU, 8GB RAM |

---

## 10. Terraform Infrastructure as Code

### `main.tf`

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
  backend "s3" {
    bucket = "idp-terraform-state"
    key    = "idp/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# ── VPC ──────────────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"

  azs              = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets  = ["10.0.10.0/24", "10.0.11.0/24"]
  database_subnets = ["10.0.20.0/24", "10.0.21.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  enable_dns_support     = true

  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = var.common_tags
}

# ── EKS Cluster ──────────────────────────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.2.1"

  cluster_name    = "${var.project_name}-eks"
  cluster_version = "1.29"

  cluster_endpoint_public_access = false  # Private cluster

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_addons = {
    coredns    = { most_recent = true }
    kube-proxy = { most_recent = true }
    vpc-cni    = { most_recent = true }
    aws-ebs-csi-driver = { most_recent = true }
  }

  eks_managed_node_groups = {
    cpu_workers = {
      name           = "cpu-workers"
      instance_types = ["m6i.4xlarge"]
      min_size       = 2
      max_size       = 20
      desired_size   = 4
      labels = { workload = "cpu" }
    }

    gpu_inference = {
      name           = "gpu-inference"
      instance_types = ["g4dn.2xlarge"]
      min_size       = 1
      max_size       = 8
      desired_size   = 2
      labels = { workload = "gpu", "nvidia.com/gpu" = "true" }
      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
      ami_type = "AL2_x86_64_GPU"
    }
  }

  tags = var.common_tags
}

# ── S3 Buckets (Document Lake) ────────────────────────────────────
resource "aws_s3_bucket" "document_bronze" {
  bucket = "${var.project_name}-raw-documents-${var.environment}"
  tags   = merge(var.common_tags, { Layer = "Bronze" })
}

resource "aws_s3_bucket" "document_silver" {
  bucket = "${var.project_name}-processed-documents-${var.environment}"
  tags   = merge(var.common_tags, { Layer = "Silver" })
}

resource "aws_s3_bucket" "document_gold" {
  bucket = "${var.project_name}-validated-records-${var.environment}"
  tags   = merge(var.common_tags, { Layer = "Gold" })
}

resource "aws_s3_bucket_versioning" "bronze_versioning" {
  bucket = aws_s3_bucket.document_bronze.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bronze_sse" {
  bucket = aws_s3_bucket.document_bronze.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.idp_key.arn
    }
  }
}

# ── KMS Key ────────────────────────────────────────────────────────
resource "aws_kms_key" "idp_key" {
  description             = "KMS key for IDP document encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = var.common_tags
}

# ── RDS PostgreSQL ─────────────────────────────────────────────────
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.3.0"

  identifier = "${var.project_name}-postgres"
  engine     = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"
  allocated_storage = 100
  max_allocated_storage = 1000

  db_name  = "idp_metadata"
  username = "idp_admin"
  manage_master_user_password = true

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  storage_encrypted   = true
  kms_key_id          = aws_kms_key.idp_key.arn
  deletion_protection = true

  backup_retention_period = 30
  backup_window           = "03:00-06:00"
  maintenance_window      = "Mon:06:00-Mon:10:00"

  tags = var.common_tags
}

# ── Amazon MSK (Kafka) ─────────────────────────────────────────────
resource "aws_msk_cluster" "idp_kafka" {
  cluster_name           = "${var.project_name}-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.2xlarge"
    storage_info {
      ebs_storage_info { volume_size = 500 }
    }
    client_subnets  = module.vpc.private_subnets
    security_groups = [aws_security_group.kafka_sg.id]
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
    encryption_at_rest_kms_key_arn = aws_kms_key.idp_key.arn
  }

  client_authentication {
    sasl { iam = true }
  }

  logging {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = "/aws/msk/${var.project_name}"
      }
    }
  }

  tags = var.common_tags
}

# ── Security Groups ─────────────────────────────────────────────────
resource "aws_security_group" "rds_sg" {
  name   = "${var.project_name}-rds-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }
  tags = var.common_tags
}

resource "aws_security_group" "kafka_sg" {
  name   = "${var.project_name}-kafka-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port       = 9098
    to_port         = 9098
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }
  tags = var.common_tags
}
```

### `variables.tf`

```hcl
variable "project_name" {
  description = "Project identifier used for all resource naming"
  type        = string
  default     = "idp-insurance"
}

variable "environment" {
  description = "Deployment environment (dev/staging/prod)"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "Primary AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "common_tags" {
  description = "Tags applied to all AWS resources"
  type        = map(string)
  default = {
    Project     = "IDP-Insurance"
    ManagedBy   = "Terraform"
    Environment = "prod"
    CostCenter  = "AI-Platform"
    Compliance  = "Insurance-Data-Governance"
  }
}

variable "gpu_instance_type" {
  description = "GPU instance type for model inference nodes"
  type        = string
  default     = "g4dn.2xlarge"
}

variable "cpu_instance_type" {
  description = "CPU instance type for worker nodes"
  type        = string
  default     = "m6i.4xlarge"
}
```

### `outputs.tf`

```hcl
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API server endpoint"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "kafka_bootstrap_brokers" {
  description = "MSK Kafka TLS bootstrap brokers"
  value       = aws_msk_cluster.idp_kafka.bootstrap_brokers_sasl_iam
  sensitive   = true
}

output "s3_bronze_bucket" {
  description = "Raw document S3 bucket name"
  value       = aws_s3_bucket.document_bronze.bucket
}

output "s3_silver_bucket" {
  description = "Processed document S3 bucket name"
  value       = aws_s3_bucket.document_silver.bucket
}

output "s3_gold_bucket" {
  description = "Validated records S3 bucket name"
  value       = aws_s3_bucket.document_gold.bucket
}

output "kms_key_arn" {
  description = "KMS key ARN for document encryption"
  value       = aws_kms_key.idp_key.arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}
```

---

## 11. CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/idp-mlops-pipeline.yml
name: IDP MLOps CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'models/**'
      - 'training/**'
      - 'kubernetes/**'
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      trigger_retraining:
        description: 'Trigger model retraining'
        required: false
        default: 'false'

env:
  AWS_REGION: us-east-1
  ECR_REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-east-1.amazonaws.com
  EKS_CLUSTER: idp-insurance-eks
  MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}

jobs:
  # ── Stage 1: Code Quality & Security ─────────────────────────────
  code-quality:
    name: Code Quality & Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Lint (Ruff)
        run: ruff check src/ training/ --select ALL

      - name: Type check (mypy)
        run: mypy src/ --strict

      - name: Security scan (Bandit)
        run: bandit -r src/ -l

      - name: Dependency vulnerability scan (Safety)
        run: safety check

      - name: Container image scan (Trivy)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'table'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'

  # ── Stage 2: Unit & Integration Tests ────────────────────────────
  tests:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    needs: code-quality
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: idp_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml --cov-fail-under=85

      - name: Run integration tests
        run: pytest tests/integration/ -v --timeout=60
        env:
          DATABASE_URL: postgresql://postgres:test_password@localhost/idp_test

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with: { files: coverage.xml }

  # ── Stage 3: Model Validation ─────────────────────────────────────
  model-validation:
    name: Model Quality Gates
    runs-on: ubuntu-latest
    needs: tests
    if: github.ref == 'refs/heads/main' || github.event.inputs.trigger_retraining == 'true'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Download evaluation dataset
        run: aws s3 cp s3://idp-insurance-eval-data/eval_set.json ./eval_set.json

      - name: Run model evaluation
        run: python training/evaluate_model.py --eval-set eval_set.json --model-uri ${{ secrets.CANDIDATE_MODEL_URI }}
        env:
          MLFLOW_TRACKING_URI: ${{ env.MLFLOW_TRACKING_URI }}

      - name: Check quality gates
        run: |
          python training/check_quality_gates.py \
            --min-f1 0.93 \
            --min-ner-f1 0.92 \
            --max-latency-ms 300 \
            --results-path eval_results.json

      - name: Register model to staging
        if: success()
        run: python training/register_model.py --stage Staging

  # ── Stage 4: Build & Push Container Images ────────────────────────
  build:
    name: Build & Push Docker Images
    runs-on: ubuntu-latest
    needs: [tests]
    strategy:
      matrix:
        service: [idp-api, preprocessing-worker, ocr-worker, fraud-scorer]
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v2

      - name: Set image tag
        id: meta
        run: echo "tag=${GITHUB_SHA::8}" >> $GITHUB_OUTPUT

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: services/${{ matrix.service }}/
          push: true
          tags: |
            ${{ env.ECR_REGISTRY }}/${{ matrix.service }}:${{ steps.meta.outputs.tag }}
            ${{ env.ECR_REGISTRY }}/${{ matrix.service }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ── Stage 5: Deploy to Staging ────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, model-validation]
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER }}

      - name: Deploy to staging namespace
        run: |
          helm upgrade --install idp-insurance ./helm/idp-chart \
            --namespace staging \
            --create-namespace \
            --set image.tag=${GITHUB_SHA::8} \
            --set environment=staging \
            --values helm/idp-chart/values-staging.yaml \
            --wait --timeout 10m

      - name: Run smoke tests
        run: pytest tests/smoke/ -v --base-url=${{ secrets.STAGING_API_URL }}

  # ── Stage 6: Canary Deploy to Production ─────────────────────────
  deploy-production-canary:
    name: Deploy Canary to Production (5%)
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER }}

      - name: Deploy canary (5% traffic)
        run: |
          helm upgrade --install idp-insurance-canary ./helm/idp-chart \
            --namespace production \
            --set image.tag=${GITHUB_SHA::8} \
            --set environment=production \
            --set canary.enabled=true \
            --set canary.weight=5 \
            --values helm/idp-chart/values-prod.yaml \
            --wait --timeout 10m

      - name: Monitor canary metrics (15 min)
        run: |
          python scripts/monitor_canary.py \
            --duration 900 \
            --error-threshold 1.0 \
            --latency-threshold-ms 3000 \
            --stp-threshold 93.0

      - name: Promote canary to full production
        if: success()
        run: |
          helm upgrade idp-insurance ./helm/idp-chart \
            --namespace production \
            --set image.tag=${GITHUB_SHA::8} \
            --set environment=production \
            --set canary.enabled=false \
            --values helm/idp-chart/values-prod.yaml \
            --wait --timeout 15m

      - name: Rollback on failure
        if: failure()
        run: helm rollback idp-insurance --namespace production
```

---

## 12. Operational Model

### Service Level Agreements (SLA)

| Metric | Target | Alert Threshold |
| :--- | :--- | :--- |
| **API Availability** | 99.9% (≤8.7 hours downtime/year) | <99.5% over 5 min window |
| **Real-time Processing Latency (p95)** | <3 seconds end-to-end | >2.5s triggers warning; >4s triggers page |
| **Batch Throughput** | >1,000 documents/hour | <800 docs/hour triggers alert |
| **STP Rate** | >95% | <93% triggers model retraining review |
| **Extraction F1 Score** | >0.92 | <0.90 triggers retraining pipeline |
| **Human Review Escalation Rate** | <5% | >8% triggers capacity alert |
| **Data Loss** | RPO: 1 hour; RTO: 4 hours | N/A — automated |

### Disaster Recovery Strategy

| Scenario | Strategy | RTO | RPO |
| :--- | :--- | :--- | :--- |
| **Single AZ failure** | Multi-AZ EKS + RDS automatic failover | <2 min | <1 min |
| **Full region failure** | S3 CRR to us-west-2; RDS snapshot restore; Route 53 health check failover | <4 hours | <1 hour |
| **Model serving failure** | Triton → Azure AI Document Intelligence fallback (managed service) | <5 min | N/A |
| **LLM serving failure** | vLLM → Azure OpenAI GPT-4o-mini fallback | <30 sec | N/A |
| **Kafka failure** | MSK multi-AZ brokers; 7-day message retention; consumer group rebalancing | <2 min | <2 min |
| **Data corruption** | S3 versioning; RDS point-in-time recovery (30 days) | <2 hours | Point in time |

### Backup Policies

| Data | Backup Frequency | Retention | Location |
| :--- | :--- | :--- | :--- |
| Raw Documents (S3 Bronze) | Continuous (versioning) + CRR | 7 years (regulatory) | S3 + us-west-2 replica |
| RDS PostgreSQL | Automated daily snapshot | 30 days | AWS Backup + cross-region copy |
| MLflow Model Registry | Daily backup | 2 years | S3 + versioning |
| Kafka Topics | 7-day retention on MSK | 7 days | MSK (durable) |
| Vector Store (Pinecone) | Daily export to S3 | 90 days | S3 Silver |
| Audit Logs | Continuous | 7 years | CloudWatch + Glacier |

### Cost Optimization

| Strategy | Implementation | Estimated Saving |
| :--- | :--- | :--- |
| **GPU Spot Instances** | Use Spot g4dn.2xlarge for batch retraining; On-Demand for inference serving | 60-70% on training costs |
| **S3 Intelligent Tiering** | Auto-transition old documents to Glacier after 90 days | 40-60% on storage costs |
| **Semantic Caching** | Redis cache for repeated document type classification queries | 15-25% on GPU inference cost |
| **Model Cascading** | Route simple structured PDFs to lightweight TF-IDF classifier; complex to LayoutLMv3 | 20-30% on GPU compute |
| **Karpenter Auto-Scaling** | Scale GPU nodes to zero during off-peak hours (2AM–6AM) | 30-40% on compute costs |
| **Batch Consolidation** | Batch OCR and preprocessing jobs; reduce per-request GPU overhead | 15-20% on preprocessing costs |
| **Right-Sizing** | Weekly compute utilization review; downsize over-provisioned node groups | 10-15% ongoing |

### AI Governance Framework

| Governance Element | Implementation |
| :--- | :--- |
| **Model Cards** | Published for every production model: training data, performance metrics, bias analysis, intended use, limitations |
| **Bias Audit** | Quarterly per-document-type performance audit; check accuracy parity across document quality levels |
| **Explainability** | SHAP values for fraud scorer; attention maps for LayoutLMv3; RAG citation trail for validation |
| **Human Oversight** | All flagged documents reviewed by Claims Adjuster; adjuster corrections fed back to active learning |
| **Data Lineage** | Full document lineage: raw S3 → OCR output → extraction JSON → validated record → claims system |
| **Access Control** | RBAC: read-only for Adjusters, write for Supervisors, full access for ML Engineers, admin for Platform team |
| **Compliance Reporting** | Monthly STP rate, accuracy, escalation rate reports to CIO/CDO; quarterly bias audit to Compliance Officer |
| **Model Change Management** | All model updates require: evaluation benchmark passing, staging deployment, canary validation, approval gate |

---

*Document generated using the [`ai-system-design-architect`](.agents/skills/ai-system-design-architect/SKILL.md) skill.*  
*Architecture diagram file: [`idp-insurance-architecture.drawio`](idp-insurance-architecture.drawio)*
