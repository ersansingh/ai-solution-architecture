# AI Algorithm & Model Recommendation Report: [Use Case Name]

---

## 1. Executive Summary

[Provide a 2-3 paragraph summary of the problem, the core AI approach recommended, key business constraints considered, expected performance, and confidence level.]

---

## 2. Business Problem Analysis

* **Business Objective**: [What the organization wants to achieve]
* **Current Process**: [How the process works today]
* **Pain Points**: [Key challenges and inefficiencies]
* **Expected Outcome**: [Measurable business results expected]
* **Success Criteria**: [Business KPIs and Technical KPIs]
* **Stakeholders**: [Primary and secondary users]
* **Constraints**: [Budget, timeline, regulatory, explainability, latency]

---

## 3. AI Suitability Assessment

Evaluate whether Machine Learning is the correct solution:

* **Alternatives Considered**: [Business rules / SQL / BI dashboards / Search / RAG / Workflow automation / Optimization / Traditional software]
* **Why ML Is Recommended**: [Specific justification for why ML provides measurable value over simpler alternatives]
* **Why ML Is NOT Recommended** (if applicable): [Recommend the simpler alternative with reasoning]

---

## 4. Problem Classification

* **ML Task Category**: [e.g., Binary Classification / Multi-Class Classification / Regression / Time-Series Forecasting / Clustering / Anomaly Detection / NLP / Computer Vision / RAG / Reinforcement Learning]
* **Data Modality**: [e.g., Structured Tabular / Unstructured Text / Image / Audio / Video / Multi-Modal / Time-Series / Graph / Streaming]
* **Learning Paradigm**: [e.g., Supervised / Unsupervised / Semi-Supervised / Self-Supervised / Transfer Learning / Reinforcement Learning / RAG / Hybrid]
* **Execution Mode**: [e.g., Real-Time Online / Near-Real-Time Micro-Batch / Offline Daily Batch / Streaming / Edge]
* **Classification Reasoning**: [Why this problem type and paradigm were selected]

---

## 5. Data Assessment

### Data Type
* [Structured / Semi-structured / Text / Images / Audio / Video / Time-Series / Graph / Streaming]

### Data Quality
* **Dataset Size**: [Row count, volume in GB/TB]
* **Features**: [Number of numerical, categorical, text, embedding features]
* **Label Availability**: [Fully labeled / Partially labeled / Unlabeled]
* **Missing Values**: [Low (<2%) / Moderate (5-15%) / High (>30%)]
* **Class Imbalance**: [Balanced / Imbalanced (ratio) / Severely Imbalanced]
* **Outliers**: [Prevalence and impact assessment]
* **Historical Depth**: [Months/years of available data]
* **Overall Data Quality**: [High / Medium / Low with reasoning]

---

## 6. Recommended Learning Paradigm

* **Selected Paradigm**: [e.g., Supervised Learning / Unsupervised Learning / RAG / Reinforcement Learning]
* **Justification**: [Why this paradigm is the best fit for the data, constraints, and business objective]
* **Alternatives Considered**: [Other paradigms evaluated and why they were not selected]

---

## 7. Top Three Algorithms

### Rank 1 (Recommended): [Algorithm/Model Name]
* **Model Category**: [e.g., Gradient Boosted Decision Tree / Transformer Encoder / SLM / Vision Transformer]
* **Specific Implementation**: [e.g., XGBoost 2.0 / LightGBM / RoBERTa-Large / Llama-3-8B-Instruct / YOLOv8]
* **Why Recommended**:
  * [Reason 1: Business fit and data suitability]
  * [Reason 2: Performance vs latency compliance]
  * [Reason 3: Explainability and production readiness]

### Rank 2 (Alternative): [Algorithm/Model Name]
* **Model Category**: [e.g., CatBoost / Random Forest / DeBERTa-v3 / Mistral-7B]
* **Why Alternative**:
  * [When to switch to this model]
  * [Key trade-off vs Rank 1]

### Rank 3 (Baseline): [Algorithm/Model Name]
* **Model Category**: [e.g., Logistic Regression / Naive Bayes / Rule-based Heuristic]
* **Purpose**: [Establish performance floor, benchmark training speed, validate pipeline]

---

## 8. Algorithm Comparison Table

| Evaluation Dimension | Rank 3 Baseline ([Model A]) | Rank 1 Recommended ([Model B]) | Rank 2 Alternative ([Model C]) |
| :--- | :--- | :--- | :--- |
| **Business Fit** | [Low / Medium / High] | [Low / Medium / High] | [Low / Medium / High] |
| **Data Suitability** | [Low / Medium / High] | [Low / Medium / High] | [Low / Medium / High] |
| **Expected Accuracy** | [Baseline metric] | [Target metric] | [Target metric] |
| **Interpretability** | [Native / High / Medium / Low] | [Native / High / Medium / Low] | [Native / High / Medium / Low] |
| **Scalability** | [Low / Medium / High] | [Low / Medium / High] | [Low / Medium / High] |
| **Training Time** | [Fast / Moderate / Slow] | [Fast / Moderate / Slow] | [Fast / Moderate / Slow] |
| **Inference Latency** | [< X ms] | [< X ms] | [< X ms] |
| **Computational Cost** | [$ / $$ / $$$ / $$$$] | [$ / $$ / $$$ / $$$$] | [$ / $$ / $$$ / $$$$] |
| **Hyperparameter Complexity** | [Low / Medium / High] | [Low / Medium / High] | [Low / Medium / High] |
| **Production Readiness** | [Low / Medium / High] | [Low / Medium / High] | [Low / Medium / High] |

---

## 9. Feature Engineering Recommendations

1. **Missing Value Handling**: [Strategy]
2. **Encoding**: [Strategy for categorical features]
3. **Scaling & Normalization**: [Strategy for numerical features]
4. **Feature Selection**: [Strategy for dimensionality reduction / relevance filtering]
5. **Feature Creation**: [Domain-specific engineered features]
6. **Outlier Handling**: [Strategy]
7. **Class Balancing**: [Strategy if applicable]
8. **Data Augmentation**: [Strategy if applicable]
9. **Domain-Specific Processing**: [Time-series lags / Text tokenization / Image preprocessing]

---

## 10. Evaluation Metrics

* **Primary Optimization Metric**: [e.g., ROC-AUC / PR-AUC / F1-Score / RMSE / RAGAS Faithfulness / mAP / Cumulative Reward]
* **Secondary Metrics**: [e.g., Precision@K, Recall@K, Log-Loss, Latency, Throughput]
* **Cross-Validation Strategy**: [e.g., Stratified K-Fold / Temporal Split / Group K-Fold]
* **Hyperparameter Tuning Framework**: [e.g., Optuna / Ray Tune]

---

## 11. Production Architecture & MLOps

* **Inference Mode**: [Batch / Real-time / Streaming]
* **Training Mode**: [Offline / Online / Incremental]
* **Feature Store**: [Feast / Tecton / Databricks]
* **Model Registry**: [MLflow / SageMaker / Vertex AI]
* **Experiment Tracking**: [MLflow / W&B / Neptune]
* **Model Serving**: [KServe / Triton / vLLM / FastAPI]
* **CI/CD Pipeline**: [GitHub Actions / GitLab CI / Azure DevOps]
* **Monitoring & Drift Detection**: [Evidently AI / Arize AI / Prometheus + Grafana]
* **Deployment Strategy**: [Canary / Blue-Green / Shadow / A/B]
* **Retraining Strategy**: [Scheduled / Drift-triggered]

---

## 12. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| [Risk 1 e.g., Data drift] | [High/Medium/Low] | [High/Medium/Low] | [Mitigation strategy] |
| [Risk 2 e.g., Overfitting] | [High/Medium/Low] | [High/Medium/Low] | [Mitigation strategy] |
| [Risk 3 e.g., Bias] | [High/Medium/Low] | [High/Medium/Low] | [Mitigation strategy] |
| [Risk 4 e.g., Latency spikes] | [High/Medium/Low] | [High/Medium/Low] | [Mitigation strategy] |

---

## 13. Implementation Roadmap

| Phase | Activities | Duration |
| :--- | :--- | :--- |
| **1. Business Understanding** | Stakeholder alignment, KPI definition | [X weeks] |
| **2. Data Collection** | Source identification, ingestion pipeline | [X weeks] |
| **3. Data Preparation** | Cleaning, deduplication, quality checks | [X weeks] |
| **4. Feature Engineering** | Transformation, encoding, feature store | [X weeks] |
| **5. Model Selection** | Baseline, candidate evaluation | [X weeks] |
| **6. Training** | Model training, cross-validation | [X weeks] |
| **7. Hyperparameter Tuning** | Optuna/Ray Tune optimization | [X weeks] |
| **8. Evaluation** | Metric validation, bias audit | [X weeks] |
| **9. Deployment** | Containerization, CI/CD, serving | [X weeks] |
| **10. Monitoring** | Drift detection, dashboards, alerting | [X weeks] |
| **11. Continuous Improvement** | Retraining automation, feedback loops | Ongoing |

---

## 14. Final Recommendation

[Summarize the final recommended approach in 2-3 sentences, including the primary algorithm, key architectural decisions, and expected business impact.]

---

## 15. Confidence Level

* **Confidence**: [High / Medium / Low]
* **Reasoning**: [Explain what drives confidence level — data quality, problem clarity, algorithm maturity, constraint alignment]
* **Key Assumptions**: [List critical assumptions that could affect the recommendation]
