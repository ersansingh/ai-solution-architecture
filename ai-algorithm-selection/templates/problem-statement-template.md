# Universal Enterprise AI Problem Statement Template

> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`  
> **Paradigm Quick Links**:
> - [Supervised Learning Template](problem-statement-supervised.md)
> - [Unsupervised Learning Template](problem-statement-unsupervised.md)
> - [Reinforcement Learning Template](problem-statement-reinforcement-learning.md)
> - [Deep Learning Template](problem-statement-deep-learning.md)
> - [Generative AI & LLM Template](problem-statement-generative-ai.md)

---

## 1. Business Objective
[Describe the high-level business goal, why this solution is being built, and what business problem it aims to solve.]

---

## 2. Business Problem & Primary AI Paradigm
Select the primary AI paradigm for this solution:
* [ ] Supervised Learning (Classification / Regression / Time Series)
* [ ] Unsupervised Learning (Clustering / Anomaly Detection / Representation Learning)
* [ ] Reinforcement Learning (Sequential Decision Making / Bandits / Policy Optimization)
* [ ] Deep Learning (Vision / Audio / Speech / Complex Multimodal)
* [ ] Generative AI & LLMs (RAG / Fine-Tuned Models / AI Agents / Prompt Engineering)

[Describe the current pain point, revenue impact, inefficiency, or challenge faced by the business in detail.]

---

## 3. Current Process
[Detail how the process is currently handled (e.g., manual processes, legacy rule-based engines, SQL scripts, spreadsheet calculations, human review).]

---

## 4. Expected Business Outcome
* [Expected outcome 1]
* [Expected outcome 2]
* [Expected outcome 3]

---

## 5. Success Criteria
Business KPIs
* [Business KPI 1 e.g., Reduce churn by 20%]
* [Business KPI 2 e.g., Increase conversion rate by 15%]

Technical KPIs
* [Technical KPI 1 e.g., Precision ≥ 85%, F1-Score ≥ 0.82 / RAGAS Faithfulness ≥ 0.90]
* [Technical KPI 2 e.g., ROC-AUC ≥ 0.90 / mAP ≥ 0.50]
* [Technical KPI 3 e.g., Inference latency < 200 ms]

---

## 6. Target Variable / Output Definition
Target Variable / Output Signal:
[Variable name or generated response schema]

Possible Values / Schema:
* [Value 1 e.g., Yes / 1 / High / JSON Schema]
* [Value 2 e.g., No / 0 / Low]

Definition:
[Exact technical and operational definition of the target variable or generation output.]

---

## 7. Business Users
Primary Users
* [User Group 1 e.g., Customer Support Specialists]
* [User Group 2 e.g., Underwriters / Risk Analysts]

Secondary Users
* [User Group 1 e.g., Executive Leadership / BI Team]
* [User Group 2 e.g., Downstream Automated Systems / API Consumers]

---

## 8. Available Data Sources
* [Data Source 1 e.g., CRM Database / Knowledge Base PDFs]
* [Data Source 2 e.g., Transaction Logs / Event Stream]
* [Data Source 3 e.g., Unstructured Text / Documents / Audio Recordings]

---

## 9. Data Characteristics
Dataset Size
* [e.g., 50 Million rows / 500 GB / 100,000 PDF documents]

Historical Data
* [e.g., 3 years of daily historical data]

Features / Schema
* [e.g., 180 structured features / Dense vector embeddings]

Label / Ground Truth Availability
* [Fully labeled / Unlabeled / Interactive environment / RAG Grounding]

Class Imbalance / Anomaly Rate
* [e.g., Balanced / 90:10 / 99.5:0.5]

Data Refresh & Frequency
* [Real-time streaming / Hourly / Daily batch / Weekly]

---

## 10. Data Quality Challenges
* [Challenge 1 e.g., Missing values or label noise]
* [Challenge 2 e.g., High feature cardinality or concept drift]

---

## 11. Business Constraints
* [Regulatory e.g., GDPR / HIPAA / Fair Lending Act / EU AI Act]
* [Explainability e.g., SHAP explanations or citation grounding required]
* [Budget e.g., Annual cloud budget capped at $250,000]

---

## 12. Technical Constraints
Training Environment: [AWS SageMaker / Azure ML / Vertex AI / On-Prem GPUs]
Programming Language: [Python 3.11 / PyTorch]
Storage / Lakehouse: [Snowflake / Delta Lake / AWS S3 / ADLS Gen2]
Serving Platform: [KServe / Triton / vLLM / FastAPI]
Monitoring: [Prometheus + Grafana / Evidently AI / Arize AI]

---

## 13. Performance Requirements
Prediction / Generation Accuracy: [Target metric threshold]
Latency SLA: [p95 < 150 ms]
Throughput: [Up to 2,000 requests per second]

---

## 14. Explainability & Governance Requirements
[Global feature importance, instance SHAP plots, or RAG context citations]

---

## 15. Security and Compliance
* [ISO 27001 / SOC 2 / Encryption / RBAC / PII Guardrails]

---

## 16. Deployment Environment
Cloud: [AWS / Azure / GCP / Hybrid]
Training: [SageMaker / Azure ML / Databricks]
Serving: [KServe / vLLM / Triton]
Feature / Vector Store: [Feast / Qdrant / Pinecone / Milvus]

---

## 17. Risks & Mitigations
Business Risks: [False positives / False negatives / Cost overruns]
Technical Risks: [Concept drift / Latency spikes / Hallucinations]

---

## 18. Expected Deliverables
* [Trained Model / Container Microservice / Batch Scoring Pipeline / Monitoring Dashboard]

---

## 19. Success Metrics
Business & Technical validation metrics.

---

## 20. Additional Notes
Operational assumptions and scalability notes.
