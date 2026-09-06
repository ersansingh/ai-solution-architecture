# Enterprise AI Capability Maturity Assessment Rubric (0 to 5)

## Overview

The Enterprise AI Capability Maturity Assessment (ACMA) evaluates an enterprise across 6 foundational pillars on a scale of **Level 0 (Absent)** to **Level 5 (Transformational / AI-First)**.

---

## 6 Capability Pillars & 5-Level Rubric

### Pillar 1: Strategy, Vision & Executive Alignment
- **Weight**: 15%
- **Level 0 (Absent)**: No AI strategy; AI seen solely as an IT experimental tool.
- **Level 1 (Exploratory / Ad-Hoc)**: Isolated AI pilots in departmental silos without executive sponsor or unified strategy.
- **Level 2 (Defined / Emergent)**: CAIO/CDAO appointed; formal enterprise AI charter created; strategic goals defined.
- **Level 3 (Operationalized)**: AI embedded in annual business unit planning; clear funding allocation and ROI targets across BUs.
- **Level 4 (Scaled / Value-Driven)**: AI portfolio management with active stage-gate funding, risk-adjusted ROI tracking, and executive dashboards.
- **Level 5 (AI-First / Transformative)**: AI is the core driver of enterprise business models, product strategies, and industry disruption.

---

### Pillar 2: Data Foundation, Quality & Semantic Layer
- **Weight**: 20%
- **Level 0 (Absent)**: Fragmented, siloed data in relational/legacy DBs with no unified governance or searchability.
- **Level 1 (Exploratory / Ad-Hoc)**: Ad-hoc CSV extraction, poor data quality, manual data prep taking 80%+ of project time.
- **Level 2 (Defined / Emergent)**: Cloud data lakehouse established; initial metadata catalog; structured ETL/ELT pipelines in place.
- **Level 3 (Operationalized)**: Automated data quality scoring, feature stores, enterprise semantic layer, and vector index pipelines.
- **Level 4 (Scaled / Value-Driven)**: Real-time streaming ingestion, automated lineage tracking, semantic knowledge graphs, and multimodal data readiness.
- **Level 5 (AI-First / Transformative)**: Self-healing, autonomous data fabrics with real-time continuous grounding and active metadata management.

---

### Pillar 3: AI Platform, MLOps/LLMOps & Tooling Infrastructure
- **Weight**: 20%
- **Level 0 (Absent)**: Local Jupyter notebooks running on developer laptops; no shared GPUs or compute clusters.
- **Level 1 (Exploratory / Ad-Hoc)**: Direct public SaaS LLM API calls with hardcoded API keys; manual ad-hoc model deployment.
- **Level 2 (Defined / Emergent)**: Standardized cloud AI development environments; centralized API Gateway with rate limiting.
- **Level 3 (Operationalized)**: Automated CI/CD for models, centralized LLM Gateway (semantic caching, fallback routing), vector DB cluster, containerized serving.
- **Level 4 (Scaled / Value-Driven)**: End-to-end MLOps/LLMOps pipelines (automated evals, drift detection, red-teaming, cost optimization/FinOps).
- **Level 5 (AI-First / Transformative)**: Multi-cloud autonomous platform with self-tuning agentic orchestrations, auto-retraining, and dynamic model routing.

---

### Pillar 4: Talent, Organization, Literacy & Culture
- **Weight**: 15%
- **Level 0 (Absent)**: Zero dedicated AI talent; high institutional fear and skepticism regarding AI automation.
- **Level 1 (Exploratory / Ad-Hoc)**: Handful of passionate enthusiasts experimenting in silos; lack of structured training.
- **Level 2 (Defined / Emergent)**: Central AI CoE formed; baseline AI literacy training rolled out for broad workforce.
- **Level 3 (Operationalized)**: Role-based training tracks (Executives, Product Managers, Citizen AI, Developers); active AI Guild.
- **Level 4 (Scaled / Value-Driven)**: Federated AI squads in each major BU; AI champions driving continuous bottom-up innovation.
- **Level 5 (AI-First / Transformative)**: Pervasive AI-augmented workforce culture; continuous learning and experimentation embedded in employee performance.

---

### Pillar 5: Governance, Ethics, Compliance & Model Risk Management (MRM)
- **Weight**: 15%
- **Level 0 (Absent)**: No AI governance; widespread unmonitored "Shadow AI" using consumer tools with company data.
- **Level 1 (Exploratory / Ad-Hoc)**: Informal awareness of AI risks; reactive handling of hallucinations or data leaks.
- **Level 2 (Defined / Emergent)**: Enterprise Acceptable Use Policy (AUP); central AI registry; initial compliance review with EU AI Act / NIST AI RMF.
- **Level 3 (Operationalized)**: 3-Lines-of-Defense model active; automated guardrails (PII scrubbing, prompt injection defense, toxicity filters); AI Ethics Board.
- **Level 4 (Scaled / Value-Driven)**: Continuous automated model observability, automated bias/fairness testing, third-party AI vendor risk audits, ISO 42001 certification.
- **Level 5 (AI-First / Transformative)**: Autonomous continuous compliance monitoring, formal model recertification/kill-switch mechanisms, regulatory sandboxing leadership.

---

### Pillar 6: Use Case Pipeline, Delivery & Value Realization
- **Weight**: 15%
- **Level 0 (Absent)**: No structured intake; random experimentation without business justification.
- **Level 1 (Exploratory / Ad-Hoc)**: "Proof of Concept graveyard" (POCs never reach production); lack of clear success metrics.
- **Level 2 (Defined / Emergent)**: Formal use case qualification funnel (Value vs. Feasibility scoring); initial production pilots.
- **Level 3 (Operationalized)**: Standardized Delivery Lifecycle (Discovery -> POC -> Pilot -> Production); tracking of operational TAT and STP %.
- **Level 4 (Scaled / Value-Driven)**: Portfolio value tracking (hard ROI, cost reduction, revenue enablement); reusable agent/workflow modules across BUs.
- **Level 5 (AI-First / Transformative)**: Autonomous product features, new AI-driven revenue streams, and self-optimizing business processes.

---

## Maturity Calculation & Scoring Formula

$$\text{Overall Maturity Score} = \sum_{i=1}^{6} (\text{Pillar Score}_i \times \text{Weight}_i)$$

### Target Transition Stages:
- **Level 0.0 – 1.4**: **Foundational Awakening** (Focus on: Policies, Sandboxes, Central CoE, Data Catalog)
- **Level 1.5 – 2.4**: **Structured Emergence** (Focus on: LLM Gateway, Use Case Funnel, Baseline Literacy, Guardrails)
- **Level 2.5 – 3.4**: **Operational Scale** (Focus on: Federated Pods, MLOps CI/CD, Enterprise RAG/Vector DB, Role Training)
- **Level 3.5 – 4.4**: **Enterprise Industrialization** (Focus on: Automated Governance, FinOps, Agentic Systems, Value Realization)
- **Level 4.5 – 5.0**: **AI-Native Transformation** (Focus on: Autonomous Self-Optimizing Systems, New Business Models)
