# Enterprise AI Problem Statement Template

> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`  
> This is a unified template covering all AI paradigms. Complete the **Universal Sections (1–20)** for every problem statement. Then complete the **Paradigm-Specific Appendix** that matches your selected AI paradigm.

---

# Part I – Universal Problem Statement (All Paradigms)

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
* [Business KPI 3 e.g., Reduce operational handling time by 30%]

Technical KPIs
* [Technical KPI 1 e.g., Precision ≥ 85%, F1-Score ≥ 0.82 / RAGAS Faithfulness ≥ 0.90]
* [Technical KPI 2 e.g., ROC-AUC ≥ 0.90 / mAP ≥ 0.50 / Cumulative Reward Lift ≥ 15%]
* [Technical KPI 3 e.g., Inference latency < 200 ms / TTFT < 500 ms]
* [Technical KPI 4 e.g., Throughput ≥ 1000 requests/sec]

---

## 6. Target Variable / Output Definition

Target Variable / Output Signal:
[Variable name, generated response schema, or policy action definition]

Possible Values / Schema:
* [Value 1 e.g., Yes / 1 / High / JSON Schema / Discrete Action Set]
* [Value 2 e.g., No / 0 / Low / Continuous Range]

Definition:
[Exact technical and operational definition of the target variable, generation output, or reward signal, including time windows or thresholds.]

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
* [Data Source 2 e.g., Transaction Logs / Event Stream / Simulator Environment]
* [Data Source 3 e.g., Unstructured Text / Documents / Images / Audio Recordings]

---

## 9. Data Characteristics

Dataset Size
* [e.g., 50 Million rows / 500 GB / 100,000 PDF documents / 150,000 annotated images]

Historical Data
* [e.g., 3 years of daily historical data / 2 years of logged interaction episodes]

Features / Schema
* [e.g., 180 structured features / Dense vector embeddings / 2048x2048 image tensors / 42 NetFlow attributes]

Label / Ground Truth Availability
* [Fully labeled / Partially labeled / Unlabeled / Interactive simulator / RAG document grounding]

Class Imbalance / Anomaly Rate / Reward Sparsity
* [e.g., Balanced / 90:10 / 99.5:0.5 / 0.1% contamination / Sparse delayed rewards]

Data Refresh & Frequency
* [Real-time streaming / Hourly / Daily batch / Weekly / On-demand]

---

## 10. Data Quality Challenges
* [Challenge 1 e.g., Missing values or label noise]
* [Challenge 2 e.g., High feature cardinality or concept drift]
* [Challenge 3 e.g., Data drift due to macroeconomic or seasonal shifts]
* [Challenge 4 e.g., Outliers and noisy sensor/log data]

---

## 11. Business Constraints
* [Regulatory e.g., GDPR / HIPAA / Fair Lending Act / EU AI Act]
* [Privacy e.g., Data must remain within sovereign cloud region]
* [Explainability e.g., Must provide SHAP explanations or citation grounding to regulators]
* [Budget e.g., Annual AI cloud infrastructure budget capped at $250,000]
* [Timeline e.g., MVP deployment required within 12 weeks]

---

## 12. Technical Constraints

Training Environment: [AWS SageMaker / Azure ML / Vertex AI / On-Prem GPUs / Custom Gym Simulator]
Programming Language: [Python 3.11 / PyTorch / R / C++]
Storage / Lakehouse: [Snowflake / Delta Lake / AWS S3 / ADLS Gen2]
Feature / Vector Store: [Feast / Qdrant / Pinecone / Milvus / Hopsworks]
Experiment Tracking: [MLflow / Weights & Biases / Neptune]
Serving Platform: [KServe / Triton Inference Server / vLLM / FastAPI]
Monitoring: [Prometheus + Grafana / Evidently AI / Arize AI]
CI/CD: [GitHub Actions / GitLab CI / Azure DevOps]

---

## 13. Performance Requirements

Prediction / Generation Accuracy: [Target metric threshold e.g., Precision ≥ 85% / mAP ≥ 0.50 / RAGAS ≥ 0.94]
Latency SLA: [p95 < 150 ms / FPS ≥ 60 / TTFT < 500 ms / Control loop < 5 ms]
Availability: [e.g., 99.9% uptime SLA]
Throughput: [Up to 2,000 requests per second / 500,000 events per second]
Model Retraining: [Automated weekly / Trigger-based on drift detection]

---

## 14. Explainability & Governance Requirements
* [Global feature importance ranking for executive reporting / SHAP / LIME]
* [Individual instance risk breakdown / Attention heatmaps / Grad-CAM]
* [RAG citation grounding with verbatim document references]
* [Bias and fairness auditing (Demographic Parity / Equalized Odds)]
* [Model card documentation and audit trail]

---

## 15. Security and Compliance
* [Compliance standard 1 e.g., ISO 27001]
* [Compliance standard 2 e.g., SOC 2 Type II]
* [Data Protection e.g., Encryption in transit (TLS 1.3) and at rest (AES-256)]
* [Access Control e.g., Role-Based Access Control (RBAC) & OAuth2 / OIDC]
* [Auditability e.g., Full log audit trail of all inference requests and outputs]
* [AI Safety e.g., PII detection, prompt injection filtering, toxicity guardrails]

---

## 16. Deployment Environment

Cloud: [AWS / Azure / GCP / Hybrid / On-Premise / Edge]
Training: [SageMaker / Azure ML / Vertex AI / Databricks / Custom GPU Cluster]
Serving: [KServe / vLLM / Triton / FastAPI / NVIDIA DeepStream]
Feature / Vector Store: [Feast / Qdrant / Pinecone / Milvus]
Model Registry: [MLflow / SageMaker Model Registry]
Streaming: [Apache Kafka / AWS Kinesis / Azure Event Hubs / Apache Flink]
Monitoring: [Prometheus / Grafana / Evidently AI / Datadog]

---

## 17. Risks & Mitigations

Business Risks: [False positives / False negatives / Cost overruns / Revenue impact]
Technical Risks: [Concept drift / Data drift / Overfitting / Feature leakage / Hallucinations]
Operational Risks: [Model degradation / Latency spikes / Upstream schema changes]
Safety Risks: [Adversarial attacks / Exploration safety (RL) / Fail-safe controls (Vision/Robotics)]

---

## 18. Expected Deliverables
* [Trained Model Artifacts / Policy Weights in Model Registry]
* [Real-time REST Inference Microservice / Streaming Scoring Pipeline]
* [Automated Batch Scoring Pipeline]
* [Model Monitoring & Drift Detection Dashboard]
* [Explainability & Feature Importance Interface / RAG Citation Viewer]
* [Automated Retraining & CI/CD Pipeline]

---

## 19. Success Metrics

Business
* [Metric 1 e.g., 15% reduction in churn rate / $1.2M annual cost savings]
* [Metric 2 e.g., 80% reduction in contract review time]

Technical
* [Metric 1 e.g., ROC-AUC > 0.90 / mAP > 0.92 / RAGAS Faithfulness > 0.94]
* [Metric 2 e.g., API latency < 200 ms at 1,000 QPS / 60 FPS edge inference]
* [Metric 3 e.g., Zero downtime deployment capability]

---

## 20. Additional Notes
[Include any operational assumptions, legacy integration notes, scalability requirements, edge cases, multi-region deployment goals, or simulator/environment constraints.]

---
---

# Part II – Paradigm-Specific Appendices

> **Instructions**: Complete ONLY the appendix that corresponds to your selected AI paradigm from Section 2 above.

---

## Appendix A – Supervised Learning Details

> Complete this appendix when the paradigm is **Supervised Learning** (Classification / Regression / Time-Series Forecasting).

### A.1 Supervised Task & Target Variable Specification
* **ML Task Type**:
  * [ ] Binary Classification
  * [ ] Multi-Class Classification
  * [ ] Multi-Label Classification
  * [ ] Continuous Regression
  * [ ] Time-Series / Sequential Forecasting
* **Target Variable Name**: `[e.g. churn_flag / total_sales / default_risk]`
* **Target Values / Range**: `[e.g. {0, 1} / Continuous $0 - $100M]`
* **Operational Target Definition**: [Exact mathematical and business definition of the label, including lookahead windows]
* **Ground Truth Availability**: [Historical labeled dataset size, labeling methodology, ground truth noise level]

### A.2 Data Characteristics & Feature Attributes
* **Feature Dimensionality**: [Number of numerical, categorical, text, and temporal features]
* **Class Balance Ratio**: [e.g., 50:50, 90:10, or 99.5:0.5 severe imbalance]
* **Data Quality & Nulls**: [Missing value percentages, noisy labels, temporal drift patterns]
* **Data Splitting Requirement**: [Stratified K-Fold / Out-of-Time Temporal Split / Group Split by Entity ID]

### A.3 Evaluation Metrics & SLAs
* **Primary Optimization Metric**: [e.g., ROC-AUC / PR-AUC / F1-Score / RMSE / MAE / MAPE]
* **Operational SLA Criteria**: [Precision at fixed recall, maximum false positive rate threshold]
* **Technical Latency SLA**: [p95 inference latency, e.g. < 50 ms]
* **Throughput SLA**: [e.g. 2,000 QPS]

### A.4 Constraints & Compliance
* **Explainability Requirements**: [Must use SHAP / LIME / TreeSHAP for regulatory transparency]
* **Compute / Budget Constraints**: [CPU only vs GPU availability, cloud training budget]
* **Regulatory Compliance**: [GDPR / HIPAA / Fair Lending Act / Credit Scoring regulations]

---

## Appendix B – Unsupervised Learning Details

> Complete this appendix when the paradigm is **Unsupervised Learning** (Clustering / Anomaly Detection / Dimensionality Reduction / Representation Learning).

### B.1 Unsupervised Task & Methodology Specification
* **Unsupervised Paradigm**:
  * [ ] Customer / Data Clustering (Group discovery)
  * [ ] Anomaly & Outlier Detection (Unlabeled novel event detection)
  * [ ] Dimensionality Reduction & Manifold Learning (Feature compression)
  * [ ] Representation Learning (Self-supervised feature extraction)
* **Cluster / Anomaly Definition**: [What constitutes a valid cluster or abnormal event in business terms]
* **Distance / Similarity Metric Preference**: [Euclidean / Cosine / Mahalanobis / Manifold distance]

### B.2 Data Characteristics
* **Data Density & Sparsity**: [Dense numerical, sparse vectors, high-dimensional embeddings]
* **Expected Anomaly Rate (Contamination Factor)**: [e.g. Estimated 0.1% to 2% anomaly rate]
* **Noise & Outlier Levels**: [High background noise, overlapping distribution clusters]

### B.3 Evaluation & Validity Metrics
* **Internal Cluster Validity Metrics**: [Silhouette Score / Davies-Bouldin Index / Calinski-Harabasz Index]
* **Anomaly Detection Performance**: [Precision@K on historical pseudo-ground-truth audit samples]
* **Reconstruction Metrics**: [Reconstruction Error / MSE for Autoencoders]
* **Latency & Throughput SLA**: [Streaming anomaly evaluation latency e.g., < 10 ms]

### B.4 Constraints & Downstream Integration
* **Interpretability**: [Must provide cluster centroid profiles or feature attribution for anomaly scores]
* **Deployment Execution**: [Batch clustering refresh vs Real-time streaming anomaly scoring]

---

## Appendix C – Reinforcement Learning Details

> Complete this appendix when the paradigm is **Reinforcement Learning** (Model-Based / Model-Free RL / Contextual Bandits / Offline RL).

### C.1 Markov Decision Process (MDP) Formulation
* **State Space ($\mathcal{S}$)**: [Vector of environment observations, historical states, agent status]
* **Action Space ($\mathcal{A}$)**:
  * [ ] Discrete Action Space (e.g. {Buy, Sell, Hold} or {Select Ad 1..N})
  * [ ] Continuous Action Space (e.g. Steering angle $[-1.0, 1.0]$, Price adjustment $[-\$50, +\$50]$)
* **Reward Function ($\mathcal{R}(s, a, s')$)**: [Exact mathematical definition of immediate reward and penalties]
* **Discount Factor ($\gamma$)**: [e.g., $\gamma = 0.99$ for long-horizon optimization]
* **Horizon Type**: [Episodic (max steps $T$) vs Continuous Infinite Horizon]

### C.2 Environment & Simulator Availability
* **Simulator Availability**: [Custom Gym/Gymnasium Environment / Physics Engine (MuJoCo/Isaac) / Historical Logged Data]
* **Environment Fidelity**: [Real-time interactive vs Offline batch log execution]
* **Exploration Safety**: [Are exploratory random actions allowed in production, or is Offline RL / Constrained RL required?]

### C.3 Performance & Evaluation Criteria
* **Target Metric**: [Cumulative Episode Return $\sum \gamma^t R_t$ / Expected Reward Lift over Baseline]
* **Sample Efficiency**: [Maximum allowed environment interactions/steps during training]
* **Safety Boundaries**: [Hard constraint violations allowed: 0 (Requires Safe RL / Shielding)]
* **Inference Latency SLA**: [Control loop frequency e.g. < 5 ms for robotics or < 50 ms for web recommendation]

### C.4 Deployment & Policy Execution
* **Learning Paradigm**: [On-Policy (PPO) / Off-Policy (SAC/DDPG) / Offline RL (CQL/IQL) / Contextual Bandit (LinUCB)]
* **Deployment Hardware**: [Edge microcontroller / GPU Server / Real-time API]

---

## Appendix D – Deep Learning Details

> Complete this appendix when the paradigm is **Deep Learning** (Computer Vision / Speech & Audio / Multi-Modal / Complex Sequential Data).

### D.1 Modality & Task Specification
* **Target Data Modality**:
  * [ ] Image / Video Data
  * [ ] Audio / Speech Signals
  * [ ] Complex Multi-Modal (Text + Image + Tabular)
  * [ ] Graph / Mesh / Spatial Data
* **Task Type**: [Classification / Object Detection / Instance Segmentation / Speech-to-Text / Feature Embedding]
* **Input Resolution / Format**: [e.g. 1080p video @ 30 FPS / 512x512 RGB images / 16kHz WAV audio]

### D.2 Dataset & Compute Characteristics
* **Training Data Size**: [Number of labeled samples, total dataset volume in GB/TB]
* **Pre-trained Backbone Availability**: [ImageNet pre-trained / COCO / Wav2Vec2 / Whisper]
* **Data Augmentation Strategy**: [Random Crop, Flip, Color Jitter, Mixup, CutMix, SpecAugment]
* **Training Hardware**: [Available GPU clusters e.g., 8x NVIDIA H100 / A100 / RTX 4090]

### D.3 Performance & Deployment SLAs
* **Accuracy Metrics**: [mAP@0.5:0.95 / Top-1 Accuracy / Dice Coefficient / Word Error Rate (WER)]
* **Inference Speed SLA**: [FPS requirement e.g. ≥ 30 FPS / Latency < 33 ms]
* **Serving Edge Constraints**: [NVIDIA Jetson / Android Mobile / TensorRT / ONNX INT8 Quantization]

### D.4 Security & Safety Constraints
* **Explainability**: [Grad-CAM / Integrated Gradients / Attention Heatmaps]
* **Safety Protocols**: [Fail-safe defaults for high-risk automated vision/speech controls]

---

## Appendix E – Generative AI & LLM Details

> Complete this appendix when the paradigm is **Generative AI & Large Language Models** (RAG / SLMs / LLMs / Multi-Agent Orchestration / Fine-Tuning).

### E.1 Generative Pattern & Model Selection Focus
* **Primary GenAI Pattern**:
  * [ ] Retrieval-Augmented Generation (RAG)
  * [ ] Fine-Tuned Small Language Model (SLM < 10B parameters)
  * [ ] Large Language Model API (GPT-4o / Claude 3.5 / DeepSeek-V3)
  * [ ] Autonomous AI Agent with Tool Execution
  * [ ] In-Context Learning & Few-Shot Prompting
* **Input Context & Documents**: [Unstructured PDFs, HTML docs, database schemas, API specs]
* **Output Format**: [Structured JSON schema / Markdown report / Multi-turn Dialogue / SQL query / Code block]

### E.2 Operational & Cost Parameters
* **Context Window Requirements**: [Average input tokens per request, max context length e.g. 16k to 128k tokens]
* **Token Economics & Cloud Budget**: [Max acceptable cost per 1M tokens, daily token volume]
* **Deployment Sovereignty**: [Cloud API allowed (OpenAI/Anthropic) vs Strictly On-Prem / Air-Gapped Private Hosting]
* **Latency SLA**: [Time-To-First-Token (TTFT) < 500 ms, throughput > 30 tokens/sec]

### E.3 Evaluation & Quality Metrics
* **RAG Evaluation Metrics**: [RAGAS Faithfulness, Answer Relevance, Context Precision, Context Recall]
* **Generation Quality Metrics**: [BLEU / ROUGE / Human Eval Pass@1 / LLM-as-a-Judge score]
* **Hallucination Tolerance**: [Zero-tolerance (Requires strict grounding and citations)]

### E.4 Governance, Safety & Tools
* **Safety Guardrails**: [NeMo Guardrails / Llama Guard for PII filtering, prompt injection, toxicity detection]
* **Tool / API Integration**: [Function calling, Vector DB search, Web browsing, SQL execution]
