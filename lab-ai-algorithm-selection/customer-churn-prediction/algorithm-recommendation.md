# AI Algorithm & Model Recommendation Report: Enterprise Customer Churn Prediction

## 1. Executive Summary & Problem Classification

### Overview
This recommendation report evaluates AI algorithms and models for the Enterprise Customer Churn Prediction solution targeting 18 million customers for a global telecommunications provider. The core objective is to predict customer churn within a 90-day window with high precision (≥85%), high recall (≥80%), and low inference latency (<500 ms) while complying with GDPR explainability regulations.

Based on the dataset characteristics (18M customers, 900M historical activity records, 240 structured numerical/categorical features, 18% class imbalance, daily batch scoring plus real-time CRM API scoring), **Gradient Boosted Decision Trees (GBDTs)**—specifically **XGBoost 2.0** and **LightGBM**—are recommended as the primary modeling solution. They provide optimal predictive power on tabular data, native class imbalance handling, high-throughput scoring, and exact local instance explainability via TreeSHAP.

### Problem Domain Classification
* **ML Task Category**: Binary Classification (Predicting Churn: Yes [1] / No [0])
* **Data Modality**: Structured Tabular Data (CRM demographics, billing history, usage analytics, support tickets, digital interaction metrics)
* **Learning Paradigm**: Supervised Learning (Historical 5-year labeled churn data)
* **Execution Mode**: Hybrid (Daily Offline Batch Scoring via Azure ML + Real-Time Online REST Inference API via KServe on AKS <500 ms)

---

## 2. Recommended AI Algorithms & Models

### Primary Recommendation: Gradient Boosted Decision Trees (XGBoost 2.0 & LightGBM)

* **Model Category**: Gradient Boosted Decision Tree (GBDT)
* **Specific Architecture/Implementation**: XGBoost 2.0 (Hist Tree Method with GPU acceleration) & LightGBM 4.0
* **Rationale for Recommendation**:
  * **Tabular SOTA Performance**: GBDTs consistently outperform deep learning networks on structured tabular datasets with heterogeneous numerical and categorical features.
  * **TreeSHAP Compliance**: Provides exact local feature attribution required for regulatory GDPR compliance and customer success representative dashboards.
  * **Class Imbalance Support**: Native support for weighted log-loss (`scale_pos_weight = 4.55`) and focal loss to handle 18% churn rate.
  * **Sub-50ms Serving**: When compiled via Treelite or ONNX Runtime, inference latency is under 20 ms per request, easily meeting the <500 ms SLA at 5,000 QPS.

### Secondary / Alternative Candidate: CatBoost

* **Model Category**: Symmetric Gradient Boosted Decision Trees
* **Rationale & Trade-offs**:
  * **High-Cardinality Handling**: Outstanding handling of high-cardinality categorical features (e.g. device model IDs, postal codes, tariff plans) without dynamic target leakage.
  * **Trade-off**: Slightly higher CPU/GPU memory consumption during model training compared to LightGBM.

### Baseline & Benchmark Model Strategy

* **Simple Baseline**: Logistic Regression with L2 Regularization (using Weight of Evidence [WoE] encoded features)
* **Purpose**: Establishes a fast, linear baseline floor (expected ROC-AUC ~0.78) to measure the non-linear gain of GBDTs and validate pipeline infrastructure.

---

## 3. Comparative Evaluation & Trade-off Matrix

| Evaluation Criteria | Baseline (Logistic Regression) | Primary (XGBoost 2.0 / LightGBM) | Alternative (CatBoost) | Advanced Deep Learning (TabNet) |
| :--- | :--- | :--- | :--- | :--- |
| **ROC-AUC Score** | 0.78 - 0.81 | **0.91 - 0.94 (Meets KPI ≥0.90)** | **0.90 - 0.93** | 0.88 - 0.91 |
| **Precision @ 0.80 Recall** | 68% | **86% (Meets KPI ≥85%)** | 85% | 81% |
| **Inference Latency (p95)** | < 2 ms | **< 15 ms (Compiled ONNX)** | < 20 ms | ~ 85 ms |
| **Training Time (900M recs)** | ~ 15 minutes | **~ 45 minutes (GPU Hist)** | ~ 90 minutes | ~ 8 hours |
| **Memory / Compute Footprint** | Minimal CPU | Low (Single GPU / 32GB RAM) | Moderate GPU VRAM | High Multi-GPU VRAM |
| **Explainability (GDPR)** | Exact Coefficients | **Exact TreeSHAP Values** | Exact TreeSHAP Values | Attention Mask Approximation |
| **Class Imbalance Handling** | Class weights | **Native `scale_pos_weight`** | Native Focal Loss | Custom Loss Function |
| **Maintenance Complexity** | Very Low | **Low** | Low | High |
| **Estimated Azure Cost / Mo** | $150 | **$850** | $1,200 | $4,500 |

---

## 4. Feature Engineering & Preprocessing Strategy

### Data Ingestion & Preprocessing Pipeline
1. **Handling Missing Values**:
   * Numerical (e.g. usage metrics): Impute using median grouped by customer subscription tier.
   * Categoricals: Treat missing as a distinct category (`"UNKNOWN"`). GBDTs handle NaN splits natively.
2. **Feature Extraction & Aggregations**:
   * **Temporal Lags**: Compute 30-day, 60-day, and 90-day rolling averages and velocity features (e.g., `% change in data usage month-over-month`).
   * **Ratio Features**: Support tickets per tenure month, billing overrun ratio (`current bill / avg 6-month bill`).
3. **Categorical Encoding**:
   * Frequency encoding for high-cardinality features (device models).
   * One-Hot Encoding for low-cardinality nominal features (contract type, payment method).
4. **Class Imbalance Strategy**:
   * Set `scale_pos_weight = (100 - 18) / 18 ≈ 4.55` in XGBoost/LightGBM.
   * Tune probability decision threshold via Precision-Recall curve analysis to achieve Precision ≥ 85% and Recall ≥ 80%.

---

## 5. Hyperparameter Tuning & Evaluation Framework

### Cross-Validation & Data Splitting
* **Splitting Scheme**: 5-Fold Stratified Group K-Fold grouped by `customer_id` and stratified by `churn_label` with a temporal out-of-time test set (most recent 3 months).
* **Leakage Prevention**: Feature scaling and aggregations computed strictly inside training folds.

### Optimization Metrics
* **Primary Optimization Metric**: ROC-AUC and PR-AUC.
* **Operational SLA Metric**: Precision at Fixed Recall = 80%.

### Optuna Hyperparameter Search Space (XGBoost)
* `max_depth`: `Int(4, 10)`
* `learning_rate`: `Float(0.01, 0.15, log=True)`
* `subsample`: `Float(0.6, 1.0)`
* `colsample_bytree`: `Float(0.5, 0.9)`
* `min_child_weight`: `Int(1, 10)`
* `scale_pos_weight`: `Float(3.5, 5.5)`

---

## 6. Model Explainability & Governance Strategy

### Explainability Implementation
* **Global Explainability**: Global SHAP Summary Plot identifying top churn drivers across the entire 18M customer base (e.g. support ticket count, data usage decline).
* **Local Instance Explainability**: Waterfall SHAP plot calculated during inference and served to the CRM frontend API so Customer Success reps see top 3 churn drivers per customer.

---

## 7. Model Optimization & Deployment Serving

### Optimization & Compilation
* Convert trained XGBoost model to **ONNX format** via `onnxmltools` or compile with **Treelite**.
* Run inference using **ONNX Runtime C++ execution engine** inside Docker microservice to achieve sub-15ms p95 latency.

### Serving Architecture
* **Real-time API**: KServe on Azure Kubernetes Service (AKS) with HPA (Horizontal Pod Autoscaler) scaling from 5 to 30 pods supporting up to 5,000 requests/sec.
* **Batch Scoring**: Azure Databricks / Azure ML daily PySpark batch job writing predictions to Azure Data Lake Gen2 and Feast Feature Store.
* **Drift Monitoring**: **Evidently AI** monitoring Data Drift (Population Stability Index [PSI] threshold > 0.2) and trigger weekly automated retraining pipelines in Azure ML.

---

## 8. Summary of Risks & Mitigation Playbook

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Concept Drift (Market Shift)** | High | High | Weekly automated retraining in Azure ML + daily PSI tracking on key usage features. |
| **Class Imbalance Threshold Drift** | Medium | High | Optimize decision probability threshold dynamically on validation fold PR-AUC instead of static 0.5. |
| **CRM API Latency Spikes** | Low | High | Serve cached churn risk scores from Feast Feature Store (Redis online store) with fallback to ONNX microservice. |
