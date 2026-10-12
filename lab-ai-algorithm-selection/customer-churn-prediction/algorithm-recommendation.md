# AI Algorithm & Model Recommendation Report: Enterprise Customer Churn Prediction (Global Telecommunications)

> **Paradigm**: Supervised Learning (Binary Classification on Structured Tabular Data)  
> **Problem Statement**: `customer-churn-prediction.md`  
> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`  
> **Template**: `.agents/skills/ai-algorithm-selector/templates/algorithm-recommendation-template.md`

---

## 1. Executive Summary

A global telecommunications provider loses about **18% of its 18 million customers each year**. Today it finds likely churners with manual SQL reports and fixed rules (for example, "no login for 30 days"). These methods flag customers too late and produce many false positives. The goal is to predict, **for every active customer each day**, how likely they are to churn **within the next 90 days**. Retention teams can then act early, focus their effort and cut annual churn from 18% to below 14%.

We recommend a **supervised binary classification model built with LightGBM**, a gradient-boosted decision tree (GBDT) library. It is trained on point-in-time feature snapshots of about 240 structured features from CRM, billing, usage, support, digital and marketing data. We recommend **CatBoost** as the alternative and **L2-regularized Logistic Regression with Weight-of-Evidence (WoE) encoding** as the baseline. LightGBM fits every stated constraint. It is the strongest model family for large, mixed-type tabular data. It runs on CPU, which matters because GPU capacity is limited. It handles missing values natively, which suits the 8% missing rate. It scores in under 10 ms per customer. **TreeSHAP** gives exact explanations for each customer, so it meets the requirement for explainable predictions. The design uses two serving paths. A **daily batch pipeline** scores all 18M customers and writes risk scores and the top SHAP drivers to the Feast online store. A **KServe real-time API on AKS** returns the cached score to the CRM in under 50 ms, or rescores on demand when fresh events arrive. Both paths stay well inside the 500 ms / 5,000 RPS SLA.

**Confidence: High** for the choice of algorithm and architecture. **Medium** for reaching every technical KPI at the same time. At an 18% churn rate, Precision ≥ 85% together with Recall ≥ 80% at one threshold is very ambitious. A churn ROC-AUC of 0.90 or more is usually reached only when strong signals (contract end, support escalations, usage decline) are well engineered. Section 10 sets out how to reframe these targets as operating points tied to campaign capacity.

---

## 2. Business Problem Analysis

* **Business Objective**: Identify customers likely to churn (terminate, or stay inactive for more than 90 consecutive days) within a 90-day horizon. This lets Marketing and Customer Success run targeted, timely retention campaigns.
* **Current Process**: Manual SQL reports, rule-based triggers (inactivity, contract expiry alerts) and reactive signals (complaints, call-center escalations).
* **Pain Points**:
  * Churn is detected **too late**, often after the decision to leave is made.
  * Rules generate **many false positives**, which wastes retention offers and budget.
  * Rules miss **hidden, multi-factor churn patterns** (for example, a gradual drop in data usage together with billing friction and a falling CSAT score).
  * No consistent risk score or explanation for frontline staff.
* **Expected Outcome**: At least 20% lower churn, 25% higher campaign conversion, 15% lower acquisition cost, 10% higher customer lifetime value (CLV) and a better NPS.
* **Success Criteria**:
  * *Business KPIs*: annual churn from 18% to below 14%; +25% retention conversion; −15% CAC; +10% CLV.
  * *Technical KPIs*: ROC-AUC ≥ 0.90; Precision ≥ 85%; Recall ≥ 80%; real-time latency < 500 ms; 99.95% availability; 5,000 predictions/sec; weekly retraining; < 3% performance degradation between retraining cycles.
* **Stakeholders**:
  * *Primary*: Customer Success, Marketing, Sales Managers, Customer Support, Executive Leadership.
  * *Secondary*: Data Science, Business Analysts, CRM Platform, Mobile Application.
* **Constraints**:
  * *Regulatory*: GDPR, ISO 27001, SOC 2, RBAC, encryption at rest and in transit, audit logging, masking of sensitive fields.
  * *Explainability*: per-customer churn drivers, feature importance, SHAP values and risk score are mandatory.
  * *Infrastructure*: Azure-only (Azure ML, ADLS Gen2, AKS + KServe, Feast, MLflow, Event Hubs, Prometheus/Grafana/Azure Monitor, GitHub Actions); **limited GPU**.
  * *Budget*: USD 600K/year AI budget cap.
  * *Extensibility*: must scale to multiple countries and new subscription products without a major redesign.

---

## 3. AI Suitability Assessment

* **Alternatives Considered**:
  | Alternative | Assessment |
  | :--- | :--- |
  | **Business rules / decision trees by hand** | Already in production. They capture single, obvious signals (inactivity, contract expiry) but fail on interactions across 240 features. They are the source of today's late detection and high false-positive rate. **Kept as guardrails and a fallback**, not as the core engine. |
  | **SQL reports / BI dashboards** | Good for describing who *has* churned and for cohort monitoring. They cannot produce a forward-looking 90-day probability for each customer. Kept for the executive KPI dashboard. |
  | **Survival analysis (Cox PH, Kaplan-Meier)** | Useful for estimating *time-to-churn* and for analytics. A classical Cox model is less accurate than GBDTs on 240 non-linear, interacting features. Considered as a complementary view (see Section 6). |
  | **Mathematical optimization** | Useful *downstream*: deciding which at-risk customers get which offer under a campaign budget. Not a replacement for risk prediction. |
  | **RAG / Generative AI** | Not suitable as the core engine. The task is a numeric risk prediction on structured data. An LLM would add latency, cost and explainability risk without improving accuracy. An LLM could later *summarize* SHAP drivers into plain-language guidance for agents (optional). |
* **Why ML Is Recommended**:
  * **Labels are available**: 5 years of historical churn outcomes across 18M customers.
  * **Many interacting signals**: churn comes from the combined effect of billing, usage trends, service quality and engagement. Supervised ML learns these patterns; hand-written rules cannot.
  * **Measurable value**: each percentage point of churn on 18M customers is about 180K customers. A model that improves targeting precision over rules directly cuts wasted offers and lost revenue.
  * **The problem is a standard fit for ML**: telecom churn is one of the most mature and well-proven ML use cases, with established tooling and patterns.
* **Why ML Is NOT Recommended**: Not applicable. ML is clearly justified. Existing rules should stay as hard overrides, for example to suppress scoring for customers in an active dispute or legal hold.

---

## 4. Problem Classification

* **ML Task Category**: **Binary Classification** (Churn = Yes/No within a 90-day horizon), with **calibrated probability output** used as a ranked risk score.
* **Data Modality**: **Structured tabular** (about 240 features) built from **time-series activity records** (900M monthly records) aggregated into snapshot features. There is also a small **unstructured text** component (support call transcripts), which is optional for Phase 2.
* **Learning Paradigm**: **Supervised Learning**.
* **Execution Mode**: **Hybrid**. A **daily offline batch** scores all 18M customers, and a **real-time online API** (< 500 ms) serves the CRM, backed by pre-computed scores and on-demand rescoring.
* **Classification Reasoning**:
  * The target is explicitly defined and binary, and historical labels exist, so this is supervised classification.
  * The business consumes a **ranked risk list** plus a **probability**, which calls for a probabilistic classifier with good calibration rather than a hard label.
  * Regression is not needed, because the target is not continuous. Forecasting is not needed, because the time dimension is handled by snapshot features and a fixed label horizon. Clustering or anomaly detection is not needed, because labels are available. All three were therefore ruled out as the *primary* framing.

---

## 5. Data Assessment

### Data Type
* **Structured / tabular**: CRM (demographics, tenure, plan, contract), billing (amounts, payment history, balance, discounts, method), usage (voice/data/SMS/roaming, device), digital (app and web sessions, feature adoption), marketing (campaign responses, email opens, offer acceptance, loyalty).
* **Time-series / event data**: 900M monthly activity records, which are converted into lag, trend and rolling-window features.
* **Unstructured text**: support call transcripts. These contain heavy PII under GDPR, so they are **deferred to Phase 2** and used only after masking, as derived sentiment and topic features.
* **Streaming**: Azure Event Hubs is available for near-real-time event features.

### Data Quality
* **Dataset Size**: 18M customers; 5 years of history; about 900M monthly activity records. Monthly snapshot training sets will contain hundreds of millions of customer-month rows. **Recommendation**: train on the most recent 24–36 months of monthly snapshots, with stratified downsampling of non-churners where needed.
* **Features**: about 240 structured features (mixed numerical and categorical). Several categoricals have medium to high cardinality (device model, plan/tariff code, region, complaint category).
* **Label Availability**: fully labeled (historical churn outcomes). The label **must be rebuilt consistently** using the 90-day definition (termination OR more than 90 consecutive days of inactivity) relative to each snapshot date.
* **Missing Values**: Moderate (about 8%), concentrated in demographics. The *fact that a value is missing* may itself predict churn, for example for prepaid or anonymous customers.
* **Class Imbalance**: Moderately imbalanced. The annual churn rate is about 18%. Because the **90-day** positive rate per snapshot will be lower (roughly 4–6% if churn is spread evenly through the year), the imbalance is **stronger than it first appears** and must be measured on the rebuilt labels.
* **Outliers**: Present in billing amounts (enterprise and family accounts, roaming spikes). Tree models are naturally robust to these; the linear baseline needs clipping.
* **Historical Depth**: 5 years. This is enough to capture seasonality and multiple product cycles. The oldest years may reflect plans and behaviors that are no longer offered.
* **Other Challenges**: duplicate customer records (entity resolution needed), inconsistent addresses, seasonal usage changes, concept drift in customer behavior.
* **Overall Data Quality**: **Medium–High**. Volume, label coverage and feature richness are excellent. Deduplication, label reconstruction and point-in-time correctness are the main data-engineering risks.

---

## 6. Recommended Learning Paradigm

* **Selected Paradigm**: **Supervised Learning (GBDT-based binary classification)**, with a calibrated probability output and per-prediction SHAP explanations.
* **Justification**:
  * Rich historical labels and well-defined structured features make this a standard supervised tabular problem.
  * On structured tabular data of this size, GBDTs consistently match or beat deep learning, train on CPU, and offer exact, fast explanations through TreeSHAP. This satisfies the constraints on limited GPU, explainability and budget together.
  * A supervised probability output plugs directly into campaign prioritization (rank by risk × CLV).
* **Alternatives Considered**:
  | Paradigm | Decision |
  | :--- | :--- |
  | **Deep Learning (TabNet, FT-Transformer, sequence models over raw events)** | Rejected as primary. It brings little or no accuracy gain over GBDTs on tabular data, needs GPU (a stated constraint), is harder to explain and costs more to run. Could be revisited for raw event-sequence modeling if GBDTs plateau. |
  | **Survival Analysis (Cox PH, Random Survival Forest, XGBoost-AFT)** | **Complementary, not primary.** It provides expected time-to-churn, which helps decide *when* to intervene. Recommended as a Phase 3 analytical add-on. |
  | **Unsupervised (clustering / anomaly detection)** | Rejected as primary because labels exist. K-Means/GMM segmentation of at-risk customers is useful *after* scoring, to design campaign personas. |
  | **Uplift / Causal ML (T-Learner, X-Learner, causal forests)** | **Recommended future extension.** Churn risk shows *who* will leave, while uplift modeling shows *who will respond* to an offer. This directly targets the "+25% campaign conversion" KPI. It needs randomized campaign holdout data, which should be collected from Phase 1. |
  | **Reinforcement Learning (bandits for offer selection)** | Out of scope for risk prediction. It could optimize offer choice later, once uplift data exists. |
  | **Generative AI / LLM** | Not suitable for the core prediction (latency, cost, explainability, GDPR). Optional: an LLM-generated plain-language summary of SHAP drivers for CRM agents. |

---

## 7. Top Three Algorithms

All candidates in the skill's classification guide were screened: Logistic Regression, Decision Tree, Random Forest, XGBoost/LightGBM/CatBoost, Naive Bayes, SVM, KNN and neural networks (MLP/TabNet/FT-Transformer).
* **Decision Tree**: too high variance and too weak on its own.
* **Naive Bayes**: its independence assumption is badly violated by correlated usage and billing features.
* **SVM (RBF) and KNN**: do not scale well to hundreds of millions of rows, and KNN cannot meet the latency target at 5,000 RPS.
* **Random Forest**: a viable model, but it is usually 1–3 AUC points below tuned GBDTs. Its large ensembles also slow inference and produce heavy model artifacts.
* **Neural networks**: rejected per Section 6.

**XGBoost** is almost interchangeable with LightGBM. LightGBM is preferred for training speed and memory efficiency at this scale.

### Rank 1 (Recommended): LightGBM Gradient-Boosted Decision Trees
* **Model Category**: Gradient Boosted Decision Tree (histogram-based, leaf-wise growth).
* **Specific Implementation**: LightGBM 4.x with the `binary` objective, `scale_pos_weight` or `is_unbalance` tuned against PR-AUC, and native categorical handling for low/medium-cardinality features. It is trained on CPU clusters in Azure ML, with distributed training through SynapseML or Dask for full-history runs. **Isotonic or Platt calibration** is fitted on a held-out out-of-time fold. **TreeSHAP** produces explanations for each customer. The model is exported to ONNX or served natively via the KServe LightGBM/MLServer runtime.
* **Why Recommended**:
  * **Business fit and data suitability**: it is the best-in-class model family for large, mixed-type tabular data with about 240 features. It handles the 8% missing values natively without imputation bias and is robust to billing outliers. Its histogram binning keeps training on hundreds of millions of snapshot rows feasible on CPU, within the limited-GPU and USD 600K constraints.
  * **Performance and latency**: expected ROC-AUC is about 0.88–0.92 with strong feature engineering, which is the most likely route to the ≥ 0.90 target. Single-row inference takes under 5 ms. With pre-computed batch scores, the real-time p99 is far below the 500 ms SLA at 5,000 RPS.
  * **Explainability and production readiness**: TreeSHAP gives exact feature attributions for each customer in milliseconds. This feeds the "primary churn drivers" shown in the CRM and the explainability dashboard. Monotonic constraints can enforce business-intuitive directions, for example "higher CSAT never increases risk". LightGBM has first-class support in MLflow, Azure ML and KServe.

### Rank 2 (Alternative): CatBoost
* **Model Category**: Gradient Boosted Decision Tree (symmetric/oblivious trees with ordered boosting).
* **Why Alternative**:
  * **When to switch**: switch if high-cardinality categoricals (device model, tariff code, region, complaint category, future multi-country product codes) drive performance. CatBoost's ordered target statistics encode them **without target leakage** and need less manual encoding. Its strong out-of-the-box defaults also lower tuning effort when new countries or products are onboarded.
  * **Trade-off vs Rank 1**: CPU training is slower (about 2–4×) at hundreds of millions of rows, and the distributed-training ecosystem on Azure is less mature. Inference is very fast thanks to symmetric trees. Accuracy is usually within ±0.5 AUC points of LightGBM. **Both should be benchmarked in Phase 5, and the winner promoted.**

### Rank 3 (Baseline): L2-Regularized Logistic Regression with WoE Encoding
* **Model Category**: Generalized Linear Model (cost-sensitive / class-weighted).
* **Purpose**:
  * Sets a **performance floor**. GBDTs must clearly beat it (expect about +0.04 to +0.08 AUC) to justify their complexity.
  * Validates the end-to-end pipeline (labels, point-in-time joins, Feast, MLflow, KServe) quickly and cheaply.
  * Gives a **fully transparent scorecard** (coefficients and WoE bins) that compliance and business stakeholders can audit directly. It also serves as a **fallback model** if the primary model's monitoring fails.

---

## 8. Algorithm Comparison Table

| Evaluation Dimension | Rank 3 Baseline (Logistic Regression + WoE) | Rank 1 Recommended (LightGBM) | Rank 2 Alternative (CatBoost) |
| :--- | :--- | :--- | :--- |
| **Business Fit** | Medium | **High** | High |
| **Data Suitability** | Medium (needs imputation, encoding, clipping; linear only) | **High** (native NaN, categorical support, outlier-robust, scales to more than 100M rows) | High (best for high-cardinality categoricals) |
| **Expected Accuracy** | ROC-AUC ~0.80–0.84; PR-AUC ~0.40–0.50 | **ROC-AUC ~0.88–0.92; PR-AUC ~0.55–0.70** | ROC-AUC ~0.88–0.92; PR-AUC ~0.55–0.70 |
| **Interpretability** | Native (coefficients / scorecard) | High (TreeSHAP, exact, per customer) | High (TreeSHAP, built-in feature interactions) |
| **Scalability** | High | **High** (distributed via SynapseML/Dask) | Medium–High (slower CPU training at this scale) |
| **Training Time** | Fast (minutes) | **Moderate** (about 1–3 h on a CPU cluster, full snapshot set) | Moderate–Slow (about 3–8 h CPU) |
| **Inference Latency** | < 1 ms | **< 5 ms** (single row) + < 10 ms SHAP | < 3 ms (single row) + < 10 ms SHAP |
| **Computational Cost** | $ | **$$** (CPU only) | $$ (CPU only) |
| **Hyperparameter Complexity** | Low | Medium (num_leaves, learning_rate, min_child_samples, regularization) | Low–Medium (strong defaults) |
| **Production Readiness** | High | **High** (MLflow, Azure ML, KServe/MLServer, ONNX) | High (MLflow, KServe custom/ONNX) |

*Expected accuracy ranges are estimates from comparable telecom churn programs, measured on an out-of-time test set. They must be confirmed in Phase 5.*

---

## 9. Feature Engineering Recommendations

1. **Missing Value Handling**:
   * GBDTs use native NaN routing, with no imputation.
   * Add explicit `is_missing_<feature>` indicators for demographic fields, because missingness itself can carry signal.
   * Logistic baseline: median imputation for numericals, plus a "Missing" category or WoE bin.
2. **Encoding**:
   * Low cardinality (plan type, payment method, contract type): native LightGBM categorical, or one-hot for the baseline.
   * Medium/high cardinality (device model, tariff code, region, complaint category): **out-of-fold target encoding** or frequency encoding for LightGBM, native ordered target statistics for CatBoost, and **WoE encoding** for the logistic baseline.
3. **Scaling & Normalization**:
   * Not required for GBDTs.
   * Logistic baseline: RobustScaler or Yeo-Johnson on skewed billing and usage features.
4. **Feature Selection**:
   * Run a variance threshold, then remove highly correlated duplicates (|ρ| > 0.95).
   * **SHAP-based pruning** and/or **Boruta-SHAP** to reduce about 240 raw features plus engineered features to a compact, stable set of about 80–150. This improves latency, drift robustness and explanation clarity.
   * Track PSI stability for each feature across time folds, and drop unstable features.
5. **Feature Creation** (domain-specific, all computed **as of the snapshot date**):
   * *Tenure and contract*: tenure in months, days to contract end, has the contract been renewed, number of plan changes or downgrades.
   * *Usage trends*: 30/60/90-day rolling means, and **ratio and slope features** (last 30 days vs prior 90 days) for voice, data, SMS and roaming. Also an *inactivity streak in days*.
   * *Billing friction*: bill shock (current bill / 6-month average), number of late payments, outstanding-balance ratio, discount expiry within N days, number of payment method changes.
   * *Service quality*: tickets in the last 30/90 days, average resolution time, repeat-complaint flag, last CSAT, CSAT trend, escalation count.
   * *Digital engagement*: trends in app and web login frequency, session duration, feature-adoption breadth, days since last login.
   * *Marketing responsiveness*: email open-rate trend, offer acceptance history, loyalty tier and points-expiry proximity.
   * *Device*: device age, end-of-life or upgrade eligibility.
   * *Phase 2 text features*: transcript-derived sentiment and complaint-topic scores. These are produced by an offline batch NLP job on masked transcripts, using a CPU-friendly DistilBERT-class model or Azure AI Language, and are stored as numeric features.
6. **Outlier Handling**:
   * GBDTs are robust to outliers, so no treatment is needed.
   * Logistic baseline: winsorize billing and usage at the 1st/99th percentiles.
   * Flag extreme billing values (`is_bill_outlier`) as a feature.
7. **Class Balancing**:
   * Prefer **loss weighting** (`scale_pos_weight` tuned against PR-AUC) over SMOTE-style synthetic oversampling, which distorts probability calibration and adds little for GBDTs.
   * Optionally downsample negatives in training to manage volume, then **re-calibrate** probabilities on an untouched, naturally distributed validation fold.
   * Choose the decision threshold **from the PR curve and the cost matrix** (cost of a retention offer vs CLV lost to churn), not at 0.5.
8. **Data Augmentation**: Not applicable to tabular churn data. Extra labeled snapshots, built with a sliding monthly window, increase effective sample size without synthetic data.
9. **Domain-Specific Processing**:
   * **Point-in-time correct training sets**: build monthly snapshots. Every feature uses only data available *before* the snapshot date, and the label covers the *following* 90 days. Feast's `get_historical_features` with event timestamps enforces this.
   * **Leakage controls**: exclude any feature that encodes the outcome, such as a disconnect-request flag, a final-bill indicator, or inactivity windows that overlap the label period.
   * **Entity resolution**: deduplicate customer records (deterministic plus fuzzy matching on masked identifiers) before labeling.
   * **Seasonality**: add calendar features (month, quarter, holiday period) and month-over-same-month-last-year ratios.

---

## 10. Evaluation Metrics

* **Primary Optimization Metric**:
  * **PR-AUC (Average Precision)** is the model-selection and tuning metric. It is the most informative metric under class imbalance and is directly tied to campaign targeting quality.
  * **ROC-AUC ≥ 0.90** is tracked as the stated acceptance KPI.
* **Secondary Metrics**:
  * **Precision and Recall at the chosen operating threshold**, measured against the 85% / 80% targets.
  * **Precision@K / Lift@Top-Decile**, where K is the number of customers retention teams can contact each week. This is the most actionable business metric.
  * **Calibration**: Brier score and Expected Calibration Error. Calibrated probabilities are required to combine risk with CLV (expected revenue at risk = P(churn) × CLV).
  * **Expected profit / cost-weighted metric**: (TP × saved CLV × offer success rate) − (FP + TP) × offer cost.
  * **Log-loss**, **F1 / F-beta** (β ≈ 0.9 to weight precision slightly), and **Accuracy** (reported only; see the note below).
  * **Operational**: p95/p99 API latency, throughput, batch completion time, feature freshness.
  * **Fairness**: equal opportunity and false-positive-rate parity across protected or sensitive groups (age band, region), to support GDPR fairness obligations.
* **KPI Feasibility Note**:
  * **Accuracy ≥ 85% is not a meaningful target.** With an 18% base rate, predicting "no churn" for everyone already gives about 82% accuracy, and on 90-day labels (about 4–6% positives) it gives about 95%. Accuracy should be replaced by PR-AUC and Precision@K as the gating metrics.
  * **Precision ≥ 85% and Recall ≥ 80% together** at one threshold usually needs ROC-AUC well above 0.95 at this prevalence.
  * Recommendation: agree on **two operating points** with the business.
    * A **high-precision tier** (≥ 85% precision) for costly offers.
    * A **high-recall tier** (≥ 80% recall) for low-cost engagement nudges.
* **Cross-Validation Strategy**:
  * **Temporal (out-of-time) validation**, not random K-Fold.
    * Train on snapshots T₀…Tₙ.
    * Validate on Tₙ₊₃ (respecting the 90-day label gap).
    * Test on a later, untouched quarter.
  * Use **rolling-origin (expanding window) backtests** across 4–6 folds to measure stability across seasons.
  * Use **group-aware splitting by customer ID** within the training period, so that the same customer's correlated snapshots do not leak across train and validation folds.
* **Hyperparameter Tuning Framework**: **Optuna** (TPE sampler with median pruning), integrated with MLflow tracking and run on Azure ML compute clusters. The objective is out-of-time PR-AUC with an early-stopping budget.

---

## 11. Production Architecture & MLOps

* **Inference Mode**: **Hybrid batch + real-time**.
  * *Daily batch*: an Azure ML pipeline scores all 18M active customers each day (about 18M × < 5 ms, parallelized on CPU, taking well under one hour). It writes the risk score, risk tier, top-5 SHAP drivers and model version to ADLS Gen2 (for analytics and dashboards) and to the **Feast online store** (Azure Cache for Redis).
  * *Real-time*: a **KServe InferenceService on AKS** behind the CRM API.
    * The default path reads the precomputed score and drivers from Feast, with a p99 under 50 ms.
    * An **on-demand rescoring path** recomputes the score with fresh streaming features (from Azure Event Hubs, for example a support call that just ended), with a p99 under 150 ms.
    * Horizontal Pod Autoscaling sized for 5,000 RPS and deployment across availability zones support the 99.95% availability target.
* **Training Mode**: **Offline**, with **weekly scheduled retraining** on a rolling 24–36-month snapshot window, as the problem statement requires. Optional warm-start is not needed, because GBDT full retraining on CPU is cheap.
* **Feature Store**: **Feast**.
  * Offline store on ADLS Gen2 / Synapse for point-in-time training joins.
  * Online store on Azure Cache for Redis for low-latency serving.
  * Streaming feature ingestion from Event Hubs.
  * One feature definition repository guarantees training-serving parity.
* **Model Registry**: **MLflow Model Registry**, integrated with Azure ML. It stores model signatures, calibration artifacts, SHAP explainer, data snapshot hash and model card. Stage gates run Staging → Production.
* **Experiment Tracking**: **MLflow** (Optuna trials, metrics for each time fold, feature-importance artifacts, fairness reports).
* **Model Serving**: **KServe on AKS** using the MLServer LightGBM runtime or an ONNX Runtime custom predictor. A transformer component handles Feast lookups, and SHAP is returned for each request.
* **CI/CD Pipeline**: **GitHub Actions**.
  * *CI*: unit tests, data-contract tests (Great Expectations), leakage checks.
  * *CT*: Azure ML pipeline trigger for training and evaluation.
  * *CD*: KServe manifest promotion after automated metric, fairness and latency gates pass, with manual approval for Production.
* **Monitoring & Drift Detection**:
  * **Prometheus + Grafana** for latency, RPS, error rate and saturation.
  * **Azure Monitor** for infrastructure and logs.
  * **Evidently AI** (scheduled job) for **PSI and KS-test** drift on each feature and on the score distribution. Alert thresholds: PSI > 0.2 on top-20 SHAP features or on score distribution.
  * Delayed-label performance tracking: realized PR-AUC and Precision@K computed once 90-day outcomes mature, with alerting on degradation above 3% to enforce the KPI.
  * Executive KPI and explainability dashboards in Power BI or Grafana.
* **Deployment Strategy**:
  * Run each new model in **shadow mode** first: it scores in parallel, and its scores are logged but not used, for 1–2 weeks.
  * Then roll it out as a **canary** (10% → 50% → 100% of CRM traffic) with automatic rollback.
  * Campaign effectiveness is measured through **A/B testing with a randomized no-offer holdout group**. This group also provides the data needed for future uplift modeling.
* **Retraining Strategy**:
  * **Scheduled weekly** retraining, as required.
  * Plus **drift-triggered** retraining when PSI or performance thresholds are breached.
  * Each new model is promoted only if it beats the current champion on out-of-time PR-AUC with no calibration or fairness regressions (champion/challenger).

---

## 12. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Feature / label leakage** (features overlapping the 90-day label window; disconnect-request or final-bill signals) | High | High | Point-in-time joins through Feast. Automated leakage tests (features with suspiciously high single-feature AUC). Strict temporal splits with a 90-day gap. Review of the top SHAP features with domain experts. |
| **Concept drift** (new plans, competitor offers, pricing changes, seasonality) | High | High | Weekly retraining. PSI/KS monitoring. Seasonal calendar features. Rolling training window. Delayed-label performance tracking. |
| **Data drift / delayed pipelines** (stale features at scoring time) | Medium | High | Feature freshness SLAs and alerts. Data contracts. Batch job retries. The API falls back to the last valid score and flags staleness. |
| **Unrealistic KPI combination** (85% precision + 80% recall + 85% accuracy) | High | Medium | Agree on two operating points tied to campaign capacity. Replace accuracy with PR-AUC and Precision@K. Report a cost-weighted profit metric. |
| **Class imbalance** (90-day positive rate lower than the annual 18%) | Medium | Medium | Tuned `scale_pos_weight`. Optimize PR-AUC. Post-hoc calibration. Cost-based thresholding. |
| **False positives** (unnecessary retention offers, discount cannibalization) | Medium | Medium | High-precision tier for expensive offers. Combine risk × CLV. Plan an uplift model to target only customers who can be persuaded. |
| **False negatives** (missed churners) | Medium | High | High-recall tier for low-cost nudges. Monitor recall on matured labels. |
| **Bias & fairness** (proxy discrimination through demographics or region) | Medium | High | Exclude or limit sensitive attributes. Run fairness audits (FPR and equal-opportunity parity) at each release. Publish model cards. Keep a human in the loop for offer decisions. |
| **GDPR / privacy** (PII in features and call transcripts) | Medium | High | Pseudonymize customer IDs. Mask sensitive fields. Minimize data collected. Document the lawful basis and a DPIA. Defer transcript use to Phase 2 with PII redaction. Apply RBAC, encryption and audit logging (ISO 27001 / SOC 2). Support the right to explanation through SHAP drivers. |
| **Duplicate / incomplete customer records** | Medium | Medium | Entity-resolution step before labeling. Missing-indicator features. Data-quality gates in CI. |
| **API latency spikes / availability** (5,000 RPS, 99.95%) | Low | High | Serve from precomputed Feast scores. HPA autoscaling. Multi-AZ AKS. Redis caching. Circuit breaker that falls back to the batch score. |
| **Budget overrun** (USD 600K cap) | Low | Medium | CPU-only training and serving, spot or low-priority Azure ML compute for tuning, right-sized AKS node pools. Estimated run cost is well under 30% of the budget. |

---

## 13. Implementation Roadmap

| Phase | Activities | Duration |
| :--- | :--- | :--- |
| **1. Business Understanding** | Confirm the 90-day churn definition and edge cases (prepaid, multi-line, business accounts). Agree the operating points (precision tier and recall tier), campaign capacity, offer costs and CLV model. Set up the randomized holdout design. Complete the DPIA and GDPR review. | 2 weeks |
| **2. Data Collection** | Build ingestion from CRM, billing, usage, support, digital and marketing into ADLS Gen2. Define data contracts. Set up Event Hubs streams for real-time events. | 3 weeks |
| **3. Data Preparation** | Entity resolution and deduplication. Address standardization. Reconstruct labels per snapshot. Data-quality checks (Great Expectations). Mask PII. | 3 weeks |
| **4. Feature Engineering** | Write about 240 base features plus trend, ratio and friction features as Feast feature views. Build point-in-time monthly snapshots. Run leakage tests. | 4 weeks |
| **5. Model Selection** | Logistic Regression + WoE baseline. LightGBM vs CatBoost benchmark on out-of-time folds. Feature selection with SHAP/Boruta. | 2 weeks |
| **6. Training** | Distributed LightGBM training on Azure ML CPU clusters. Rolling-origin backtests. Probability calibration. | 2 weeks |
| **7. Hyperparameter Tuning** | Optuna search (PR-AUC objective) with MLflow tracking. Tune `scale_pos_weight` and thresholds. | 1–2 weeks |
| **8. Evaluation** | KPI validation at the agreed operating points. Calibration, fairness and bias audit. Stakeholder review of SHAP explanations. Write the model card. | 2 weeks |
| **9. Deployment** | Daily batch scoring pipeline. KServe InferenceService on AKS with Feast integration. GitHub Actions CI/CD. Load test at 5,000 RPS. Shadow, then canary rollout. CRM integration. | 3 weeks |
| **10. Monitoring** | Evidently drift jobs. Prometheus/Grafana and Azure Monitor dashboards. Delayed-label performance tracking. Explainability and executive KPI dashboards. | 2 weeks |
| **11. Continuous Improvement** | Weekly retraining automation. Champion/challenger. A/B campaign measurement. Phase 2 transcript features. Phase 3 survival and uplift models. Multi-country rollout. | Ongoing |

**Indicative timeline**: about 6 months to first production release. Some phases run in parallel; for example, Phases 2–4 overlap and Phase 10 is built during Phase 9.

---

## 14. Final Recommendation

Deploy a **LightGBM binary churn classifier** trained on point-in-time monthly snapshots of about 240 structured features.
* It uses calibrated probabilities, cost-sensitive thresholds and **TreeSHAP per-customer explanations**.
* It is served through a **daily batch scoring pipeline plus a KServe-on-AKS real-time API backed by the Feast online store**.
* It is retrained weekly under MLflow governance, with Evidently drift monitoring.

**CatBoost** should be benchmarked as the alternative, and **WoE Logistic Regression** kept as both the baseline and a transparent fallback. The design runs on CPU only, which suits the limited GPU capacity, fits easily within the USD 600K budget, and meets the explainability, GDPR and 500 ms latency requirements. Combining risk with CLV, and later adding uplift modeling, is the most direct route to cutting churn from 18% to below 14% and lifting campaign conversion by 25%.

---

## 15. Confidence Level

* **Confidence**: **High** for the paradigm, algorithm and architecture choice. **Medium** for reaching every technical KPI at the same time.
* **Reasoning**:
  * Telecom churn on structured data is a mature, well-proven problem class, and GBDTs are the established state of the art for it.
  * The data is large, labeled and feature-rich.
  * The organization's existing stack (Azure ML, Feast, MLflow, KServe, GitHub Actions) maps directly onto the recommended design.
  * Uncertainty is concentrated in the **target values**, not the approach: ROC-AUC ≥ 0.90 together with ≥ 85% precision and ≥ 80% recall at one threshold is optimistic for 90-day churn. It also depends on how much signal the engineered trend and service-quality features capture.
* **Key Assumptions**:
  * Historical churn labels can be rebuilt accurately using the 90-day definition at each snapshot date, and the true 90-day positive rate will be confirmed during Phase 3.
  * Source systems carry reliable event timestamps that allow point-in-time correct feature joins.
  * The "≥ 85% accuracy" requirement can be redefined as PR-AUC / Precision@K targets, and the business accepts tiered operating thresholds.
  * Call transcripts are excluded from the initial model pending GDPR review, so only structured features are used in Phase 1.
  * Retention campaigns will keep a randomized holdout group, so that model impact (and later uplift) can be measured causally.
  * Customer behavior patterns from the most recent 24–36 months are representative of the near future, apart from drift handled by weekly retraining.
