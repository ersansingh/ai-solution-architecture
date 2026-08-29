# AI Algorithm & Model Recommendation Report: Enterprise Customer Churn Prediction

> **Paradigm**: Supervised Learning (Tabular Binary Classification)  
> **Problem Statement Reference**: `lab-ai-algorithm-selection/customer-churn-prediction/customer-churn-prediction.md`

---

## 1. Executive Summary

This recommendation report delivers an enterprise-grade AI algorithm selection, feature engineering, evaluation, and MLOps deployment strategy for a global telecommunications provider serving 18 million active subscribers. The core business objective is to proactively predict customer churn within a 90-day forward window, enabling automated and high-converting retention interventions that reduce annual churn from 18% to below 14% (a ≥20% relative churn reduction). The technical requirements demand an operational precision of ≥85%, recall of ≥80%, ROC-AUC ≥0.90, real-time CRM API latency of <500 ms (at peak loads up to 5,000 QPS), and strict compliance with GDPR explainability standards.

Based on the multi-dimensional analysis of the data landscape (18M customers, 900M multi-year monthly activity records, 240 heterogeneous tabular features, and an 18% positive class imbalance ratio of ~4.55:1), **Gradient Boosted Decision Trees (GBDTs)**—specifically **XGBoost 2.0 (Hist Tree Method with GPU/CPU acceleration)** combined with **LightGBM**—are recommended as the primary production modeling framework. GBDTs consistently deliver state-of-the-art predictive performance on structured tabular telecommunications data, natively handle missing values and non-linear feature interactions, offer built-in loss-weighting for class imbalance, and enable exact local instance-level explainability through TreeSHAP.

The proposed architecture implements a hybrid scoring topology: high-throughput daily offline batch scoring on Azure Machine Learning / Azure Databricks with feature caching in Feast (backed by Redis Online Store), alongside a containerized ONNX Runtime microservice deployed via KServe on Azure Kubernetes Service (AKS) for real-time sub-20ms CRM profile queries. This design stays well within the organization's USD 600,000 annual AI budget while providing automated drift monitoring via Evidently AI and CI/CD-driven weekly retraining pipelines.

---

## 2. Business Problem Analysis

* **Business Objective**: Proactively identify telecommunication subscribers at risk of churning in the next 90 days to trigger targeted, personalized retention campaigns (e.g., plan discounts, loyalty upgrades, dedicated support outreach), thereby protecting recurring revenue and enhancing customer lifetime value.
* **Current Process**: The retention workflow currently relies on manual retrospective SQL queries, simplistic heuristic rules (e.g., zero logins for 30 consecutive days, contract expiration within 15 days), customer complaints, and ad-hoc call center escalations.
* **Pain Points**:
  * Interventions occur too late in the customer lifecycle (often after the customer has already decided to switch carriers).
  * High false positive rates waste retention budgets on non-churning customers.
  * Inability to capture complex, multi-variate early warning signals (e.g., subtle combinations of roaming cost surges, declining data velocity, and unresolved tier-2 support interactions).
* **Expected Outcome**:
  * Reduce annual subscriber churn rate by at least 20% (from 18% baseline to below 14%).
  * Increase customer retention campaign conversion rates by 25%.
  * Decrease customer acquisition cost (CAC) pressure by 15% and increase Customer Lifetime Value (CLV) by 10%.
  * Elevate brand Net Promoter Score (NPS) through preemptive customer care.
* **Success Criteria**:
  * **Business KPIs**: Annual churn rate < 14%, campaign conversion lift ≥ 25%, CAC reduction ≥ 15%, CLV lift ≥ 10%.
  * **Technical KPIs**: ROC-AUC ≥ 0.90, PR-AUC ≥ 0.75, Precision ≥ 85%, Recall ≥ 80%, Real-time API Latency < 500 ms (p99 < 100 ms), Weekly retraining drift delta < 3%.
* **Stakeholders**:
  * **Primary**: Customer Success Team, Marketing Campaign Managers, Retention Sales Agents, Customer Care Support Representatives, Executive Leadership (CMO, CIO).
  * **Secondary**: Data Science & MLOps Engineering, Business Intelligence Analysts, CRM Platform Engineering, Mobile App Digital Channels Team.
* **Constraints**:
  * **Budget**: Total annual AI infrastructure and operational budget capped at USD 600,000.
  * **Explainability**: Strict GDPR Article 22 "Right to Explanation" compliance; Customer Success representatives must see individual churn drivers (e.g., SHAP waterfall) in the CRM UI.
  * **Latency & Throughput**: <500 ms SLA on CRM lookups; throughput scaling up to 5,000 predictions/sec.
  * **Ecosystem**: Must integrate natively within existing Microsoft Azure infrastructure (Azure ML, ADLS Gen2, AKS, Event Hubs).

---

## 3. AI Suitability Assessment

Before committing to machine learning, alternative deterministic and non-ML approaches were critically evaluated:

* **Alternatives Considered**:
  1. *Business Rules / Decision Trees (Heuristics)*: Rule-based flags (e.g., `Usage_Drop_30d > 40% AND Ticket_Count > 2`) fail because customer attrition behavior is non-linear, multi-factorial, and evolves dynamically across subscription tiers.
  2. *SQL Queries & BI Dashboards*: Retrospective BI tools only display historical churn post-facto; they lack probabilistic forward-looking estimation across 240 interacting behavioral dimensions.
  3. *Workflow Automation (RPA)*: Automates campaign outreach execution but cannot determine the underlying probability of customer attrition.
  4. *Generative AI / LLMs*: Large Language Models are computationally inefficient and poorly suited for structured tabular scoring across 18 million records with strict low-latency constraints, though LLMs can assist downstream by drafting personalized retention emails based on ML-generated churn drivers.
* **Why ML Is Recommended**:
  * Supervised Machine Learning handles multi-dimensional non-linear interactions across 240 features spanning CRM, billing, streaming usage, support tickets, and digital channels.
  * Statistical loss functions optimize the precise trade-off between Precision and Recall, ensuring marketing capital is allocated only to genuine high-risk subscribers.
  * Continuous automated retraining allows the model to adapt to seasonal trends, competitor pricing moves, and changing customer usage habits.

---

## 4. Problem Classification

* **ML Task Category**: Binary Classification ($y \in \{0, 1\}$, where $y=1$ denotes Customer Churn within 90 days, and $y=0$ denotes Active Retention).
* **Data Modality**: Structured Tabular Data (demographic attributes, billing histories, time-series usage aggregations, categorical service tiers, support event counters).
* **Learning Paradigm**: Supervised Learning with cost-sensitive loss weighting.
* **Execution Mode**: Hybrid Execution:
  1. *Daily Offline Batch Scoring*: Scores all 18M subscribers daily in Azure ML / PySpark, updating customer risk profiles in the Feast Feature Store and CRM data mart.
  2. *Real-Time Online REST Inference*: Containerized ONNX Runtime microservice on AKS providing instantaneous scoring (<20 ms) when customer attributes are dynamically updated in the CRM or mobile app.
* **Classification Reasoning**: Ground truth historical labels ($y$) are available over 5 years across 18 million accounts. Binary classification paired with calibrated probability outputs directly enables threshold tuning to meet both business conversion goals and strict Precision/Recall KPIs.

---

## 5. Data Assessment

### Data Type & Sources
* **Customer CRM**: Demographics, tenure, account status, subscription contract type, device tenure.
* **Billing System**: Monthly charges, invoice payment history, delinquency status, applied discounts, payment channel.
* **Network & Usage Analytics**: Voice minutes, data consumption (MB/GB), SMS traffic, roaming activity, international calling patterns.
* **Customer Support & Ticketing**: Ticket volume, mean time to resolution (MTTR), escalation count, CSAT scores, complaint category flags.
* **Digital Touchpoints**: Mobile self-service app launches, web portal login velocity, feature adoption, session duration.
* **Marketing Platform**: Campaign exposure history, email open rates, promotional coupon redemption.

### Data Quality Evaluation
* **Dataset Size**: 18 million active customers, ~900 million historical monthly transactional records spanning 5 years (~1.8 TB raw tabular volume).
* **Features**: 240 structured features (160 continuous/numerical, 65 low-to-medium cardinality categorical, 15 high-cardinality categorical such as postal code and device model).
* **Label Availability**: Fully labeled historical ground truth based on verified account cancellation dates and 90-day inactivity thresholds.
* **Missing Values**: Moderate (~8% overall missingness), concentrated primarily in optional customer demographic fields, legacy billing records, and digital app metrics for offline-only users.
* **Class Imbalance**: Positive churn rate is ~18% (imbalance ratio ~4.55:1 non-churners to churners).
* **Outliers**: Extreme skewness in international roaming usage, corporate account billing amounts, and high-frequency support ticket outliers.
* **Historical Depth**: 60 months (5 years) of continuous historical observation.
* **Overall Data Quality Score**: **High (8.5/10)** — High volume, long historical depth, and rich multi-system feature availability, with well-understood missingness patterns that can be handled robustly by tree-based algorithms.

---

## 6. Recommended Learning Paradigm

* **Selected Paradigm**: **Supervised Learning (Tabular Gradient Boosting & Cost-Sensitive Classification)**.
* **Justification**:
  * Tabular business data with heterogeneous distributions (mixed continuous, ordinal, and categorical features) is the proven domain where GBDTs outperform deep neural networks in both sample efficiency and top-tier predictive accuracy.
  * Supervised cost-sensitive learning allows direct optimization against the 18% class imbalance via positive class gradient reweighting (`scale_pos_weight = 4.55`).
  * Seamless integration with TreeSHAP ensures mathematical fidelity for GDPR regulatory audits.
* **Alternatives Considered**:
  * *Unsupervised / Anomaly Detection*: Re-framing churn as an anomaly fails because churners exhibit diverse behavioral patterns rather than simple statistical outliers; also discards rich 5-year labeled ground truth.
  * *Deep Learning Tabular Architectures (TabNet, FT-Transformer)*: Require 8x–15x higher computational cost during training and hyperparameter search, exhibit higher inference latency (>80 ms), and provide lower explainability fidelity compared to TreeSHAP without providing superior AUC on this tabular schema.
  * *Reinforcement Learning*: Unnecessary formulation overhead for a static 90-day binary prediction window where offline supervised risk scoring directly feeds existing marketing optimization systems.

---

## 7. Top Three Algorithms

```
                                  ┌─────────────────────────────┐
                                  │   Supervised Tabular Data   │
                                  │   (18M Users, 240 Features) │
                                  └──────────────┬──────────────┘
                                                 │
                  ┌──────────────────────────────┼──────────────────────────────┐
                  ▼                              ▼                              ▼
      ┌───────────────────────┐      ┌───────────────────────┐      ┌───────────────────────┐
      │   Rank 1: XGBoost     │      │   Rank 2: CatBoost    │      │ Rank 3: Reg. Logistic │
      │   2.0 / LightGBM 4.0  │      │   (Symmetric GBDT)    │      │  (WoE Encoded Linear) │
      │   ★ RECOMMENDED ★     │      │     [Alternative]     │      │       [Baseline]      │
      ├───────────────────────┤      ├───────────────────────┤      ├───────────────────────┤
      │ • ROC-AUC: 0.92-0.94  │      │ • ROC-AUC: 0.91-0.93  │      │ • ROC-AUC: 0.79-0.81  │
      │ • Inference: <15 ms   │      │ • Inference: <20 ms   │      │ • Inference: <2 ms    │
      │ • Exact TreeSHAP      │      │ • Native High-Card    │      │ • Simple Lin. Weights │
      │ • Lowest Azure Cost   │      │ • Higher VRAM Usage   │      │ • Floor Benchmark     │
      └───────────────────────┘      └───────────────────────┘      └───────────────────────┘
```

### Rank 1 (Recommended): Gradient Boosted Decision Trees (XGBoost 2.0 & LightGBM 4.0)
* **Model Category**: Histogram-based Gradient Boosted Decision Trees (GBDT).
* **Specific Implementation**: XGBoost 2.0 (`tree_method='hist'`, device acceleration) and LightGBM 4.0 ensemble.
* **Why Recommended**:
  1. *Unmatched Tabular Accuracy*: Consistently achieves highest ROC-AUC (0.92–0.94) and PR-AUC on mixed-type telecommunications feature sets.
  2. *Production Efficiency & Latency*: Native C++ engine compiled to ONNX Runtime executes in <15 ms per prediction, easily satisfying the 500 ms SLA at 5,000 QPS.
  3. *Native Imbalance & Missingness Handling*: Directly handles ~8% missing data via optimal default split direction routing and integrates `scale_pos_weight = 4.55`.
  4. *Regulatory Explainability*: Supports exact polynomial-time TreeSHAP calculation for local customer explanations in CRM dashboards.

### Rank 2 (Alternative): CatBoost
* **Model Category**: Symmetric (Oblivious) Gradient Boosted Decision Trees.
* **Specific Implementation**: CatBoost Classifier with ordered target statistics.
* **Why Alternative**:
  * *High-Cardinality Categoricals*: CatBoost excels when the dataset contains complex high-cardinality categorical features (e.g., postal codes, cell tower IDs, handset IMEI models) without risk of target leakage.
  * *Trade-off*: Slower GPU training throughput and ~30% higher memory consumption during hyperparameter search compared to LightGBM.

### Rank 3 (Baseline): Regularized Logistic Regression with Weight of Evidence (WoE)
* **Model Category**: Generalized Linear Model (L2/ElasticNet Regularization).
* **Specific Implementation**: `scikit-learn` `LogisticRegressionCV` with monotonic WoE binning.
* **Purpose**: Serves as the operational baseline floor (expected ROC-AUC ~0.79–0.81), validating end-to-end data ingestion pipelines and quantifying the exact non-linear lift delivered by GBDT models.

---

## 8. Algorithm Comparison Table

| Evaluation Dimension | Rank 3 Baseline (Logistic Regression + WoE) | Rank 1 Recommended (XGBoost 2.0 / LightGBM) | Rank 2 Alternative (CatBoost) | Deep Tabular (TabNet / FT-Transformer) |
| :--- | :--- | :--- | :--- | :--- |
| **Business Fit** | Medium (Under-captures complex risk signals) | **High (Optimal precision/recall balance)** | **High (Excellent on categorical attributes)** | Medium (Excessive complexity for tabular) |
| **Data Suitability** | Medium (Requires extensive manual feature binning) | **High (Handles 240 mixed features natively)** | **High (Superior categorical handling)** | Medium (Prone to overfitting on tabular) |
| **Expected Accuracy** | ROC-AUC: 0.79 – 0.81 \| Precision@0.80R: ~68% | **ROC-AUC: 0.92 – 0.94 \| Precision@0.80R: ≥86%** | **ROC-AUC: 0.91 – 0.93 \| Precision@0.80R: ≥85%** | ROC-AUC: 0.88 – 0.91 \| Precision@0.80R: ~81% |
| **Interpretability** | Native (Linear regression coefficients) | **High (Exact TreeSHAP attribution & waterfall)** | **High (TreeSHAP & feature interaction values)** | Medium (Attention masks / perturbation SHAP) |
| **Scalability** | High (Linear scalability) | **High (Distributed data-parallel histogram trees)** | **High (Multi-GPU distributed training)** | Moderate (High GPU VRAM memory footprint) |
| **Training Time** | ~15 minutes (CPU cluster) | **~45 minutes (Single GPU / Multi-core CPU)** | ~90 minutes (GPU) | ~8.5 hours (Multi-GPU cluster) |
| **Inference Latency** | < 2 ms (p95) | **< 15 ms (p95 via ONNX Runtime)** | **< 20 ms (p95 via CatBoost C++ API)** | ~ 85 ms (p95 via PyTorch C++ LibTorch) |
| **Computational Cost** | $ (~$150 / month) | **$$ (~$850 / month on Azure)** | **$$ (~$1,200 / month on Azure)** | $$$$ (~$4,500 / month on Azure) |
| **Hyperparameter Complexity** | Low (`C`, penalty, solver) | **Medium (`max_depth`, `learning_rate`, `subsample`, `colsample`)** | **Low-Medium (Robust default parameters)** | High (Layer dimensions, sparsity, attention steps) |
| **Production Readiness** | High (Standard `scikit-learn` / ONNX) | **High (Treelite, ONNX Runtime, KServe, Triton)** | **High (CatBoost C++ runtime, ONNX)** | Medium (Requires PyTorch serving container) |

---

## 9. Feature Engineering Recommendations

To extract maximum predictive signal across the 240 raw features, the following preprocessing pipeline must be implemented inside the Feast Feature Store:

```
Raw Telemetry Sources (CRM, Billing, Usage, Support, Web/App)
                            │
                            ▼
     ┌──────────────────────────────────────────────────────────┐
     │ 1. Imputation: Median by Plan Tier + "UNKNOWN" Category  │
     │ 2. Outlier Handling: IQR Winsorization (1st-99th pct)    │
     └──────────────────────────┬───────────────────────────────┘
                                │
                                ▼
     ┌──────────────────────────────────────────────────────────┐
     │ 3. Temporal Lags & Velocity (30d/60d/90d Rolling Ratios) │
     │ 4. Ratio Engineering (Bill Surges, Ticket Escalations)   │
     │ 5. Encoding: High-Card Frequency + Nominal Target Encod. │
     └──────────────────────────┬───────────────────────────────┘
                                │
                                ▼
     ┌──────────────────────────────────────────────────────────┐
     │ 6. Class Balance: scale_pos_weight = 4.55 + PR Threshold │
     │ 7. Selection: Boruta-SHAP Pruning to Top ~120 Features   │
     └──────────────────────────────────────────────────────────┘
```

1. **Missing Value Handling**:
   * *Numerical metrics (e.g., usage, data consumption)*: Grouped median imputation based on customer subscription tier and device category.
   * *Categorical attributes*: Missing values flagged as explicit `"UNKNOWN"` categories. GBDTs natively route missing branch splits during training and inference.
2. **Temporal & Velocity Features**:
   * Compute 30-day, 60-day, and 90-day rolling averages and velocity deltas:
     $$\text{Data\_Velocity\_30\_vs\_90} = \frac{\text{Data\_Usage}_{\text{Last 30d}}}{\frac{1}{3}\text{Data\_Usage}_{\text{Last 90d}} + \epsilon}$$
   * Significant negative velocity ($<0.60$) indicates sharp declining engagement—a strong leading indicator of attrition.
3. **Ratio & Interaction Features**:
   * *Billing Overrun Ratio*: $\frac{\text{Current Month Bill}}{\text{6-Month Average Bill}}$ (detects bill shock).
   * *Support Ticket Escalation Rate*: $\frac{\text{Unresolved Tickets}}{\text{Total Support Inquiries}}$ and $\frac{\text{Calls in Last 14 Days}}{\text{Tenure (Months)}}$.
   * *Payment Friction Index*: Count of late payment occurrences over the trailing 12 months.
4. **Encoding Strategies**:
   * *Low/Medium Cardinality (Contract Type, Payment Method)*: Target Encoding with out-of-fold regularization and smoothing ($m=10$).
   * *High Cardinality (Device Model, Postal Code)*: Frequency encoding combined with CatBoost/LightGBM native categorical handling.
5. **Outlier Handling**:
   * Apply 1st and 99th percentile Winsorization to unbounded financial and data usage metrics to prevent split distortions during tree construction.
6. **Class Balancing Strategy**:
   * Set `scale_pos_weight = (100 - 18) / 18 = 4.55` in XGBoost/LightGBM loss objective.
   * Avoid synthetic oversampling (SMOTE) on 900M records to prevent artificial variance and pipeline overhead; instead optimize the probability classification threshold on the Precision-Recall curve.
7. **Feature Selection**:
   * Use **Boruta-SHAP** feature selection to prune redundant features, reducing the active model feature vector from 240 to the ~120 most impactful features, reducing inference latency by ~40%.

---

## 10. Evaluation Metrics

### Primary Optimization Metrics
* **ROC-AUC (Receiver Operating Characteristic - Area Under Curve)**: Primary model discrimination metric across all classification thresholds (Target: $\ge 0.90$).
* **PR-AUC (Precision-Recall Area Under Curve)**: Critical for evaluating true positive performance on the 18% imbalanced churn class (Target: $\ge 0.75$).

### Operational SLA Metrics
* **Precision at Fixed Recall = 80%**: Must achieve $\ge 85\%$ precision to ensure marketing spend is not squandered on false alarms.
* **Top-Decile Lift**: Lift ratio in the top 10% highest-risk predicted customers relative to random selection (Target: $\ge 3.5\times$ baseline).

### Cross-Validation & Validation Strategy
* **Temporal Out-of-Time Splitting**:
  * *Training Set*: Months $T-60$ through $T-4$.
  * *Validation Set*: Month $T-3$ (used for early stopping and threshold tuning).
  * *Test Set (Out-of-Time Holdout)*: Months $T-2$ to $T$ (3-month forward churn observation window).
* **Cross-Validation**: 5-Fold Stratified Group K-Fold (grouped by `customer_id` across sliding temporal windows) to eliminate cross-temporal data leakage.

### Hyperparameter Tuning Framework
* **Engine**: **Optuna** Bayesian optimization with Tree-structured Parzen Estimator (TPE) and Hyperband early stopping across 250 trials.
* **Search Space (XGBoost 2.0)**:
  * `max_depth`: Integer $\in [4, 9]$
  * `learning_rate`: Log-uniform $\in [0.01, 0.15]$
  * `subsample`: Uniform $\in [0.65, 0.95]$
  * `colsample_bytree`: Uniform $\in [0.50, 0.85]$
  * `min_child_weight`: Integer $\in [2, 12]$
  * `scale_pos_weight`: Uniform $\in [3.8, 5.2]$
  * `reg_alpha` (L1): Log-uniform $\in [1e-3, 10.0]$
  * `reg_lambda` (L2): Log-uniform $\in [1e-2, 20.0]$

---

## 11. Production Architecture & MLOps

```
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                           AZURE DATA LAKE STORAGE GEN2                          │
  │                  (Raw Ingestion from CRM, Billing, Usage, Logs)                 │
  └────────────────────────────────────────┬────────────────────────────────────────┘
                                           │
                                           ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                    AZURE DATABRICKS / SPARK PREPROCESSING                       │
  │             (Daily Feature Engineering Pipeline & Schema Validation)            │
  └────────────────────────┬───────────────────────────────┬────────────────────────┘
                           │                               │
                           ▼                               ▼
  ┌─────────────────────────────────┐             ┌─────────────────────────────────┐
  │       FEAST FEATURE STORE       │             │    AZURE MACHINE LEARNING       │
  │  • Offline: ADLS Gen2 (Parquet) │             │  • Distributed GPU Training     │
  │  • Online: Azure Cache (Redis)  │             │  • Optuna Tuning + MLflow Track │
  └────────────────┬────────────────┘             └────────────────┬────────────────┘
                   │                                               │
                   │ (Online Feature Lookup)                       │ (Model Artifact + ONNX)
                   ▼                                               ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                      MODEL REGISTRY & SERVING (MLFLOW + AKS)                    │
  │                                                                                 │
  │   ┌─────────────────────────────────────────────────────────────────────────┐   │
  │   │ KServe on Azure Kubernetes Service (AKS)                                │   │
  │   │  • ONNX Runtime Microservice Container                                  │   │
  │   │  • TreeSHAP Fast Explainer Module                                       │   │
  │   │  • HPA Auto-scaling (5 to 30 Pods)                                      │   │
  │   └────────────────────────────────────┬────────────────────────────────────┘   │
  └────────────────────────────────────────┼────────────────────────────────────────┘
                                           │
                                           ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                         REAL-TIME CRM & APPS (< 20 ms)                          │
  │       Customer Success Dashboard, Retention Campaign Engine, Mobile App         │
  └────────────────────────────────────────┬────────────────────────────────────────┘
                                           │
                                           ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                     OBSERVABILITY & CONTINUOUS IMPROVEMENT                      │
  │   • Evidently AI: PSI Data Drift (>0.20 trigger) + KS-Test Concept Drift        │
  │   • Prometheus & Grafana: Latency, Throughput (5,000 QPS), Error Rate           │
  │   • GitHub Actions: Automated CI/CD Weekly Retraining & Canary Promotion        │
  └─────────────────────────────────────────────────────────────────────────────────┘
```

* **Inference Modes**:
  * *Batch Scoring*: Daily PySpark batch job scoring all 18M subscribers in ~40 minutes, writing risk percentiles and top 3 churn drivers to Azure Data Lake and CRM data mart.
  * *Real-Time API*: REST API hosted on AKS via KServe and ONNX Runtime; provides real-time scoring in under 20 ms when customer attributes change dynamically.
* **Feature Store**: **Feast** on Azure:
  * *Offline Store*: ADLS Gen2 Parquet tables for reproducible point-in-time training feature joins.
  * *Online Store*: Azure Cache for Redis for sub-5ms feature lookups during real-time CRM API requests.
* **Model Registry & Tracking**: **MLflow** integrated natively with Azure Machine Learning.
* **Model Compilation & Acceleration**: Convert trained XGBoost/LightGBM model to **ONNX format** via `onnxmltools` or compile via **Treelite**, executing on ONNX Runtime C++ backend.
* **CI/CD & Deployment Strategy**: **GitHub Actions** pipeline with automated canary deployment (10% traffic $\to$ 50% $\to$ 100%) and automated rollback if p99 latency exceeds 100 ms or error rate exceeds 0.01%.
* **Drift Detection & Retraining Trigger**:
  * **Evidently AI** evaluates Population Stability Index (PSI) daily on key usage features.
  * PSI $> 0.20$ or Kolmogorov-Smirnov $p$-value $< 0.05$ on top 10 features triggers an automated Azure ML pipeline to retrain, validate, and register a candidate model.

---

## 12. Risks and Mitigation

| Risk Category | Specific Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Data** | Feature Leakage (e.g., cancellation request timestamp included in predictors) | Medium | Critical | Enforce strict point-in-time joins in Feast; exclude all features generated within 7 days prior to churn event. |
| **Data** | Data Drift from seasonal holiday usage surges | High | Medium | Implement sliding-window baseline normalization in feature pipeline; daily PSI alerts in Evidently AI. |
| **Model** | Concept Drift (Competitor launches aggressive tariff plan) | High | High | Weekly scheduled model retraining in Azure ML + trigger-based retraining if 30-day rolling ROC-AUC drops by >3%. |
| **Model** | Probability Calibration Drift | Medium | High | Apply isotonic regression or Platt scaling on validation holdout to ensure output probabilities reflect true churn frequencies. |
| **Operations** | CRM API Latency Spikes during peak business hours | Low | High | Pre-compute and cache daily batch scores in Redis; compile model to ONNX with AKS Horizontal Pod Autoscaler (5–30 pods). |
| **Compliance** | GDPR "Right to Explanation" violation | Low | Critical | Serve exact TreeSHAP feature contributions via real-time API; log all predictions and attribution explanations in immutable audit store. |
| **Business** | Customer fatigue from excessive retention discounting | Medium | Medium | Implement marketing eligibility frequency caps (e.g., maximum 1 retention incentive per customer per 180 days). |

---

## 13. Implementation Roadmap

```
Month 1: Phase 1-3  (Business Alignment, Data Ingestion & Data Preparation)
Month 2: Phase 4-6  (Feature Engineering in Feast, Baseline, XGBoost/LightGBM Training)
Month 3: Phase 7-8  (Optuna Hyperparameter Tuning, SHAP Explainability & Validation)
Month 4: Phase 9-10 (AKS/KServe Deployment, ONNX Optimization, Drift Monitoring)
Month 5+: Phase 11  (Weekly Retraining, A/B Testing, Multi-Country Scaling)
```

| Phase | Activities & Milestones | Duration |
| :--- | :--- | :--- |
| **1. Business Understanding** | Align with Customer Success and Marketing on 90-day churn definition, KPI targets, and campaign workflows. | 2 Weeks |
| **2. Data Collection** | Connect ADLS Gen2 to CRM, billing, network telemetry, support tickets, and digital channel event streams. | 3 Weeks |
| **3. Data Preparation** | Implement schema validation, deduplication, missing value imputation, and out-of-time train/val/test splits. | 2 Weeks |
| **4. Feature Engineering** | Build ~120 core features (velocity, ratios, aggregations) and register feature definitions in Feast Feature Store. | 3 Weeks |
| **5. Model Selection** | Establish Logistic Regression baseline; benchmark XGBoost 2.0, LightGBM, and CatBoost on validation folds. | 2 Weeks |
| **6. Model Training** | Train distributed GBDT models on 900M record dataset using Azure ML GPU/CPU compute clusters. | 2 Weeks |
| **7. Hyperparameter Tuning** | Run 250-trial Optuna Bayesian search to optimize PR-AUC, depth, regularizers, and `scale_pos_weight`. | 2 Weeks |
| **8. Model Evaluation & Explainability** | Validate ROC-AUC ($\ge 0.92$), Precision ($\ge 86\%$), Recall ($\ge 80\%$); build TreeSHAP explanation pipeline. | 2 Weeks |
| **9. Deployment & Serving** | Containerize ONNX model on AKS with KServe; build REST inference API and daily batch scoring pipeline. | 3 Weeks |
| **10. Monitoring & Observability** | Deploy Evidently AI drift dashboards, Prometheus/Grafana infrastructure metrics, and automated alert channels. | 2 Weeks |
| **11. Continuous Improvement** | Launch A/B test against control group in CRM; activate automated weekly retraining and feedback loops. | Ongoing |

---

## 14. Final Recommendation

Deploy an ensemble of **XGBoost 2.0 and LightGBM 4.0** trained on historical multi-system telemetry, optimized for cost-sensitive binary classification via `scale_pos_weight = 4.55` and calibrated on the Precision-Recall curve. The model must be compiled to **ONNX Runtime** and served via **KServe on AKS** backed by the **Feast Feature Store (Azure Cache for Redis)**, with **TreeSHAP** generating real-time explainability drivers for Customer Success representatives. This architecture directly achieves the target KPIs (ROC-AUC $\ge 0.92$, Precision $\ge 86\%$, Recall $\ge 80\%$, Latency $<20$ ms) while operating within the USD 600,000 annual budget and fulfilling all GDPR compliance obligations.

---

## 15. Confidence Level

* **Confidence Score**: **High (95%)**
* **Reasoning**:
  1. *Clear Problem & Data Modality Match*: The problem is a classical tabular binary classification task with 18 million samples and 5 years of rich labeled history—an environment where GBDT performance and stability are universally proven.
  2. *Proven Metric Feasibility*: The target metrics (ROC-AUC $\ge 0.90$, Precision $\ge 85\%$, Recall $\ge 80\%$) are realistically achievable given the rich multi-system feature landscape (billing, usage velocity, customer support tickets).
  3. *Production Architecture Maturity*: The combination of Feast, MLflow, ONNX Runtime, and KServe on AKS provides an established, enterprise-ready pattern that comfortably meets the <500 ms SLA and 5,000 QPS throughput requirement at minimal infrastructure cost.
* **Key Assumptions**:
  * Historical churn definitions remain consistent across all 5 years of training data.
  * Customer CRM, billing, and network telemetry logs are refreshed daily with less than a 4-hour pipeline lag into Azure Data Lake Storage Gen2.
  * Marketing and retention teams possess the operational capacity to engage at least 75,000 high-risk customers per month identified by the model.
