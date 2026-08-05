## 1. Business Objective
Next-Generation Fintech Advisory Platform focused on mortgage lifecycle management and intelligent investment optimization. To maximize retail user portfolio health and platform engagement by deploying an adaptive recommendation engine that dynamically balances structural home loan prepayments with systematic investment plan (SIP) wealth accumulation.

---

## 2. Business Problem & Primary AI Paradigm

Select the primary AI paradigm for this solution:

* [ ] Supervised Learning (Classification / Regression / Time Series)
* [ ] Unsupervised Learning (Clustering / Anomaly Detection / Representation Learning)
* [x] Reinforcement Learning (Sequential Decision Making / Bandits / Policy Optimization) *(Primary orchestrator)*
* [ ] Deep Learning (Vision / Audio / Speech / Complex Multimodal)
* [ ] Generative AI & LLMs (RAG / Fine-Tuned Models / AI Agents / Prompt Engineering)

Retail fintech users frequently struggle with the capital allocation dilemma: whether to accelerate mortgage payments to reduce interest burden or invest surplus liquidity into mutual funds for compounding returns. The current lack of personalized, mathematically optimized advice leads to sub-optimal financial outcomes, delayed debt clearance, and reduced asset under management (AUM) growth on the platform, ultimately causing user disengagement.

---

## 3. Current Process

Users are currently subjected to generic, rule-based marketing nudges ("Start an SIP today" or "Pay off your loan faster"). Financial modeling is done manually by the users using disconnected spreadsheet calculators, lacking real-time integration with their actual cash flows, salary timelines, or changing macroeconomic interest rates.

---

## 4. Expected Business Outcome

* Increase platform user retention and daily active engagement through highly personalized financial insights.
* Grow SIP Assets Under Management (AUM) by identifying the optimal threshold where investing outperforms prepaying debt for specific user cohorts.
* Enhance loan portfolio health by accelerating risk-adjusted prepayments when market returns are low or individual user debt-to-income ratios enter high-risk territories.

---

## 5. Success Criteria

Business KPIs

* Increase 12-month user retention rate by 20%.
* Increase average monthly SIP contribution per active user by 15%.
* Achieve a 25% lift in conversion rates on personalized push notification nudges compared to the baseline rule-based engine.

Technical KPIs

* Cumulative Reward Lift (user wealth growth + platform engagement) ≥ 18% over the baseline system in A/B testing.
* Inference latency < 150 ms for real-time recommendation retrieval during Next.js frontend load times.
* Regression prediction accuracy (RMSE) for future cash flow surplus within a 5% error margin.

---

## 6. Target Variable / Output Definition

Target Variable / Output Signal:
`optimal_advisory_action`

Possible Values / Schema:

* Discrete Action Set: `[trigger_sip_increase, trigger_lump_sum_prepayment, trigger_emi_step_up, hold_and_monitor]`
* JSON Schema mapping the action to a specific personalized messaging payload and financial value (e.g., `{"action": "trigger_lump_sum_prepayment", "recommended_amount_inr": 250000}`).

Definition:
The exact operational policy action executed by the Deep Q-Network (DQN) at a given monthly interval, optimized to maximize the combined reward signal of the user's projected 5-year net worth and immediate 30-day platform interaction.

---

## 7. Business Users

Primary Users

* Retail Fintech Customers (interacting via the consumer application).
* Internal Wealth Advisory / Customer Success Teams.

Secondary Users

* Marketing and Growth Teams (leveraging cohorts for campaign targeting).
* Risk & Underwriting Analysts.

---

## 8. Available Data Sources

* Core banking transaction logs and event streams via API integrations.
* Unstructured PDF/image documents (uploaded bank statements, salary slips, and existing mutual fund folios).
* Historical mortgage amortization schedules and interest rate fluctuation logs.

---

## 9. Data Characteristics

Dataset Size

* ~10 Million historical user profiles; over 500 GB of transactional event logs; ~5 Million unstructured financial documents.

Historical Data

* 4 years of historical transaction and interaction episode data.

Features / Schema

* 120 structured financial features (e.g., Debt-to-Income, SIP velocity, discretionary spend ratios) and embedded document vectors.

Label / Ground Truth Availability

* Interactive simulator environment utilizing historical market data to approximate user wealth states, plus delayed sparse rewards from actual user conversion events.

Class Imbalance / Anomaly Rate / Reward Sparsity

* Highly sparse and delayed rewards (a successful property payoff or long-term wealth goal takes years to realize).

Data Refresh & Frequency

* Daily batch processing for cohort clustering and regression updates; real-time streaming for DQN state updates and OCR ingestion.

---

## 10. Data Quality Challenges

* High noise and varying formats in OCR extraction from diverse bank statements.
* Missing or masked folio numbers in third-party mutual fund aggregations.
* Feature drift due to sudden macroeconomic shifts (e.g., repo rate changes impacting floating home loan EMIs).

---

## 11. Business Constraints

* Regulatory: Strict adherence to RBI/SEBI guidelines regarding automated financial advisory and fair lending practices.
* Privacy: All personally identifiable information (PII) and financial data must remain localized within Indian sovereign cloud regions.
* Explainability: Recommendations must be transparent. The system cannot act as a "black box" when advising a user to move large sums of capital.
* Timeline: MVP backend API integration required within 16 weeks.

---

## 12. Technical Constraints

Training Environment: Custom Gym Simulator for RL; Vertex AI / AWS SageMaker for Deep Learning/Regression batch training.
Programming Language: Python 3.11 (PyTorch) for model development; TypeScript (NestJS) for application backend.
Storage / Lakehouse: Delta Lake / AWS S3.
Feature / Vector Store: Feast.
Experiment Tracking: MLflow.
Serving Platform: FastAPI for ML microservices, orchestrated and consumed by the core NestJS backend.
Monitoring: Prometheus + Grafana.
CI/CD: GitHub Actions / GitLab CI.

---

## 13. Performance Requirements

Prediction / Generation Accuracy: Cumulative Expected Reward Lift > 15%; CNN OCR extraction F1-Score ≥ 0.94.
Latency SLA: ML API p95 response < 150 ms to ensure seamless Next.js frontend rendering.
Availability: 99.95% uptime SLA for the advisory endpoint.
Throughput: Up to 1,500 requests per second during peak end-of-month salary crediting days.
Model Retraining: Reinforcement Learning policy updated weekly; Regression and Clustering models retrained monthly.

---

## 14. Explainability & Governance Requirements

* Individual instance risk breakdown using SHAP to generate human-readable explanations (e.g., "We recommended this ₹5 Lakh prepayment because your floating interest rate jumped by 0.5%").
* Model card documentation detailing cohort demographics to ensure no bias in wealth-building advice across different income brackets.
* Full audit trail logging for every recommendation payload served.

---

## 15. Security and Compliance

* Compliance standard: ISO 27001.
* Data Protection: Encryption in transit (TLS 1.3) and at rest (AES-256) for all financial data.
* Access Control: Strict Role-Based Access Control (RBAC) via OAuth2 / OIDC for all microservice communications.
* Auditability: Comprehensive log audit trail of all inference requests, generated nudges, and user responses.

---

## 16. Deployment Environment

Cloud: AWS (AP-South-1, Mumbai Region).
Training: Custom GPU Cluster / EC2 instances for RL simulation.
Serving: FastAPI microservices containerized via EKS, sitting behind the NestJS API Gateway.
Feature / Vector Store: Feast deployed on managed PostgreSQL/Redis.
Model Registry: MLflow.
Streaming: Apache Kafka for event-driven architecture (transaction ingestion).
Monitoring: Datadog (Next.js/NestJS app layers) + Evidently AI (Model drift).

---

## 17. Risks & Mitigations

Business Risks: Providing suboptimal advice that causes a user to face liquidity crunches. *Mitigation: Implement hard safety bounds (e.g., never recommend prepaying if emergency fund < 6 months expenses).*
Technical Risks: Concept drift if market conditions shift rapidly. *Mitigation: Automated drift detection triggering immediate fallback to conservative, rule-based advisory.*
Operational Risks: Latency spikes between the ML microservices and the NestJS backend. *Mitigation: Aggressive caching of user states and pre-computed recommendations during off-peak hours.*

---

## 18. Expected Deliverables

* Deep Learning OCR pipeline for document ingestion.
* Trained K-Means / DBSCAN clustering model artifacts for user segmentation.
* Trained XGBoost regression pipelines for cash flow forecasting.
* Optimized DQN policy weights deployed in the Model Registry.
* Real-time REST Inference Microservice (FastAPI) integrated with the NestJS backend.
* Model Monitoring & Drift Detection Dashboard.

---

## 19. Success Metrics

Business

* 20% reduction in user churn at the 12-month mark.
* 15% aggregate increase in SIP contributions among the active user base.

Technical

* End-to-end recommendation API latency < 200 ms at 1,000 QPS.
* Zero downtime deployment capability for policy updates.

---

## 20. Additional Notes

The architecture will operate sequentially: The deep learning module structures incoming payload data asynchronously. Background cron jobs run the clustering and regression models to update the user's state in the feature store. Finally, the Next.js frontend calls the NestJS backend, which requests the real-time optimal action from the Reinforcement Learning API based on the user's freshly updated state vector.

---

---

# Part II – Paradigm-Specific Appendices

## Appendix C – Reinforcement Learning Details

### C.1 Markov Decision Process (MDP) Formulation

* **State Space ($\mathcal{S}$)**: A continuous and categorical vector representing the user's financial health. Features include current LTV (Loan-to-Value) ratio, remaining loan tenure, monthly surplus liquidity (regression output), user cluster ID, current SIP AUM, and prevailing market repo rates.
* **Action Space ($\mathcal{A}$)**:
* [x] Discrete Action Space: `{trigger_sip_increase, trigger_lump_sum_prepayment, trigger_emi_step_up, hold_and_monitor}`


* **Reward Function ($\mathcal{R}(s, a, s')$)**: A composite function: $w_1 * (\Delta \text{Projected Net Worth}_{5yr}) + w_2 * (\text{User Interaction Flag})$. Immediate positive reward if the user clicks and executes the nudge; heavily weighted delayed reward based on the simulated optimization of their debt/equity mix.
* **Discount Factor ($\gamma$)**: $\gamma = 0.95$ (balancing the need for immediate platform engagement with long-term wealth optimization).
* **Horizon Type**: Episodic (max steps $T = 360$ months, representing a standard 30-year financial planning horizon).

### C.2 Environment & Simulator Availability

* **Simulator Availability**: Custom Python-based financial simulator utilizing historical market returns, inflation indices, and mortgage amortization math to project the outcome of the agent's actions over time.
* **Environment Fidelity**: Offline batch log execution for initial training, combined with high-fidelity financial mathematical simulations.
* **Exploration Safety**: Constrained RL is strictly required. Exploratory random actions that violate liquidity safety margins (e.g., recommending a prepayment that drops cash below a 3-month emergency threshold) are programmatically masked and assigned an immediate penalty reward of -100.

### C.3 Performance & Evaluation Criteria

* **Target Metric**: Expected Reward Lift over Baseline (Comparing the DQN's recommended 5-year wealth accumulation versus the baseline strategy of standard EMIs + standard SIPs).
* **Sample Efficiency**: System must reach policy convergence within 5 million simulated episodes.
* **Safety Boundaries**: Hard constraint violations allowed: 0. (Requires strict action masking via a deterministic safety shield before serving the recommendation to the NestJS backend).
* **Inference Latency SLA**: Decision retrieval < 50 ms.

### C.4 Deployment & Policy Execution

* **Learning Paradigm**: Offline RL (CQL) initialized on historical user data, transitioning to Off-Policy (SAC/DQN) learning continually from live user interaction feedback loops.
* **Deployment Hardware**: GPU server for offline training; CPU-based containerized instances for real-time inference via FastAPI.