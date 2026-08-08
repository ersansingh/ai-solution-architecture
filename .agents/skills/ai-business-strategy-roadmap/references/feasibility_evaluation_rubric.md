# Multi-Factor Feasibility Assessment Rubric

This reference guide provides standard criteria for scoring an enterprise AI initiative across the 4 core feasibility pillars on a 1–10 scale.

---

## 1. Technical Feasibility (Weight: 30%)

Evaluates algorithmic readiness, model capability, compute constraints, and integration difficulty.

| Score Range | Descriptor | Technical Criteria |
| :---: | :--- | :--- |
| **9–10** | **Commodity / Plug-and-Play** | Standard off-the-shelf APIs (e.g. GPT-4o, Claude 3.5 Sonnet, Whisper) or proven open models; low latency requirements; well-understood prompt design. |
| **7–8** | **Standard Integration** | RAG architecture with standard vector DB; light fine-tuning (LoRA); standard REST API integration. |
| **5–6** | **Moderate Complexity** | Multi-agent orchestration, hybrid search pipelines, custom embedding tuning, or high-throughput batch execution. |
| **3–4** | **High Technical Risk** | Custom deep learning model training from scratch; stringent real-time sub-50ms latency constraints; specialized hardware requirements. |
| **1–2** | **Unproven / R&D** | Requires novel research or non-existent algorithmic capabilities; unproven frontier AI architecture. |

---

## 2. Data Feasibility (Weight: 30%)

Evaluates data accessibility, quality, labeling status, privacy boundaries, and historical depth.

| Score Range | Descriptor | Data Criteria |
| :---: | :--- | :--- |
| **9–10** | **Ready & Structured** | Abundant, clean, well-indexed enterprise data; automated ETL; existing ground-truth labels; zero PII exposure. |
| **7–8** | **Accessible with Pipeline** | Centralized data lakehouse; requires minor cleanup, PII masking, or automated chunking pipelines. |
| **5–6** | **Siloed / Unstructured** | Data stored across disparate databases or legacy systems; moderate data cleaning and manual ground-truth annotation needed. |
| **3–4** | **Poor Quality / Sparse** | Significant missing historical data; manual labeling required for thousands of samples; unverified data accuracy. |
| **1–2** | **No Viable Data** | Data does not exist, is restricted by legal barriers, or requires multi-year data collection before model training. |

---

## 3. Operational Feasibility (Weight: 20%)

Evaluates workflow integration, user adoption readiness, skills availability, and change management.

| Score Range | Descriptor | Operational Criteria |
| :---: | :--- | :--- |
| **9–10** | **Seamless Workflow Fit** | Natural copilot UI within existing software (Slack/Teams/CRM); strong executive sponsorship; enthusiastic end-users. |
| **7–8** | **Manageable Adoption** | Requires minor workflow adjustment (e.g. human-in-the-loop sidebar); standard training sessions needed. |
| **5–6** | **Moderate Resistance** | Changes core daily operational workflows; requires significant staff retraining and ongoing user enablement. |
| **3–4** | **High Resistance / Skill Gap** | Displaces existing job roles; deep cultural resistance; lack of internal AI skills to maintain system. |
| **1–2** | **Operational Mismatch** | Incompatible with operational culture or team structure; high probability of user abandonment. |

---

## 4. Regulatory & Compliance Feasibility (Weight: 20%)

Evaluates legal risk, data privacy (GDPR/HIPAA), EU AI Act risk classification, IP protection, and safety guardrails.

| Score Range | Descriptor | Compliance Criteria |
| :---: | :--- | :--- |
| **9–10** | **Minimal Regulatory Risk** | Internal operational tool; low EU AI Act risk classification; fully anonymized data; clear IP ownership. |
| **7–8** | **Standard Managed Risk** | Handles customer data under standard GDPR/SOC2 compliance; robust PII redaction and audit logging implemented. |
| **5–6** | **High Audit Burden** | Financial or healthcare advisory; high EU AI Act classification requiring formal risk assessment and logging. |
| **3–4** | **Critical Liability Risk** | Autonomous decision-making affecting individuals (e.g. credit scoring, hiring); high legal exposure. |
| **1–2** | **Non-Compliant / Prohibited** | Violates privacy laws or EU AI Act unacceptable risk categories; intolerable legal liability. |

---

## 5. Overall Feasibility Score Calculation

$$\text{Overall Score} = (0.30 \times \text{Tech}) + (0.30 \times \text{Data}) + (0.20 \times \text{Ops}) + (0.20 \times \text{Reg})$$

$$\text{Probability of Success } (P_s) = \frac{\text{Overall Score}}{10} \times 100\%$$
