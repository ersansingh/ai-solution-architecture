# Supervised Learning Problem Statement Template

> **Paradigm**: Supervised Learning (Classification / Regression / Time-Series Forecasting)  
> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`

---

## 1. Business Objective & Problem Definition
* **Business Objective**: [High-level strategic goal, business context, and problem to solve]
* **Target Domain**: [e.g., Financial Risk / Customer Churn / Demand Forecasting / Fraud / Predictive Maintenance]
* **Current Baseline**: [e.g., Manual rule engine / Heuristic SQL scripts / Legacy linear model]

---

## 2. Supervised Task & Target Variable Specification
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

---

## 3. Data Characteristics & Feature Attributes
* **Dataset Scale**: [Row count, GB/TB size, e.g., 20M rows]
* **Feature Dimensionality**: [Number of numerical, categorical, text, and temporal features]
* **Class Balance Ratio**: [e.g., 50:50, 90:10, or 99.5:0.5 severe imbalance]
* **Data Quality & Nulls**: [Missing value percentages, noisy labels, temporal drift patterns]
* **Data Splitting Requirement**: [Stratified K-Fold / Out-of-Time Temporal Split / Group Split by Entity ID]

---

## 4. Evaluation Metrics & Success Criteria
* **Primary Optimization Metric**: [e.g., ROC-AUC / PR-AUC / F1-Score / RMSE / MAE / MAPE]
* **Operational SLA Criteria**: [Precision at fixed recall, maximum false positive rate threshold]
* **Technical Latency SLA**: [p95 inference latency, e.g. < 50 ms]
* **Throughput SLA**: [e.g. 2,000 QPS]

---

## 5. Constraints & Compliance
* **Explainability Requirements**: [Must use SHAP / LIME / TreeSHAP for regulatory transparency]
* **Compute / Budget Constraints**: [CPU only vs GPU availability, cloud training budget]
* **Regulatory Compliance**: [GDPR / HIPAA / Fair Lending Act / Credit Scoring regulations]
