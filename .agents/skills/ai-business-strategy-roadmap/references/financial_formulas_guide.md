# Financial & Risk-Adjusted Modeling Guide

This reference document details the mathematical models, formulas, and financial methodologies used in the **`ai-business-strategy-roadmap`** skill.

---

## 1. Total Cost of Ownership (TCO) Model

The 12-Month Total Cost of Ownership ($TCO$) combines initial Capital Expenditure ($Capex$) and ongoing annual Operational Expenditure ($Opex$):

$$TCO = Capex + Opex_{12M}$$

### Capital Expenditure ($Capex$) Components
- **Architecture & Scoping**: Upfront enterprise architecture, security design, and data audit.
- **Data Engineering**: Data pipeline construction, ETL, and feature store initialization.
- **Model Fine-Tuning & Prompt Harnessing**: Dataset preparation, LoRA/fine-tuning runs, and prompt pipeline development.
- **System Integration**: Microservice API creation, UI integration, and security/RBAC implementation.

### Operational Expenditure ($Opex$) Components (12-Month Projection)
- **Model API & Compute Costs**: LLM token consumption fees, GPU instance hosting (e.g., AWS EC2 g5/p4, Azure NC series).
- **Vector Database & Storage**: Vector DB cluster hosting (Pinecone, Qdrant, Milvus) and cloud blob storage (S3/GCS).
- **Maintenance & Operations**: MLOps monitoring, model re-training cycles, software licensing, and operational support.

---

## 2. Benefit Modeling & Unadjusted ROI

### Expected Annual Benefits ($B$)
Expected annual financial benefits combine direct savings and indirect productivity gains:

$$B = B_{direct} + B_{indirect}$$

- **Direct Benefits ($B_{direct}$)**: Direct labor cost reduction, third-party software license replacement, error penalty reductions.
- **Indirect Benefits ($B_{indirect}$)**: Additional throughput capacity, improved customer retention/NPS, faster turnaround time value.

### Net Benefits ($NB$)
$$NB = B - TCO$$

### Unadjusted ROI ($\text{ROI}$)
$$\text{ROI} = \left( \frac{B - TCO}{TCO} \right) \times 100\% = \left( \frac{NB}{TCO} \right) \times 100\%$$

### Payback Period ($PP$)
$$PP = \left( \frac{TCO}{B / 12} \right) \text{ months}$$

---

## 3. Risk-Adjusted Financial Return Metrics

Traditional ROI ignores technical and adoption failure probabilities. Risk-adjusted metrics incorporate the overall **Probability of Success ($P_s$)** derived from the Multi-Factor Feasibility Assessment.

### Probability of Success ($P_s$) Formula
Given weighted feasibility score $F \in [1, 10]$:

$$P_s = \frac{F}{10}$$

### Risk-Adjusted Expected Benefits ($B_{r}$)
$$B_{r} = B \times P_s$$

### Risk-Adjusted ROI ($r\text{-ROI}$)
$$r\text{-ROI} = \left( \frac{B_{r} - TCO}{TCO} \right) \times 100\% = \left( \frac{(B \times P_s) - TCO}{TCO} \right) \times 100\%$$

### Expected Monetary Value ($\text{EMV}$)
$\text{EMV}$ calculates expected net financial value, balancing successful net gains against downside capital exposure ($C_{downside}$, typically equal to initial $Capex$ or Gate 0+1 capital):

$$\text{EMV} = \left( P_s \times (B - TCO) \right) - \left( (1 - P_s) \times C_{downside} \right)$$

---

## 4. Stage-Gate Capital Release Model

To de-risk capital deployment, total budget is released in 4 sequential tranches tied to verifiable technical and business milestones:

| Horizon | Capital % | Typical Allocation Focus | Target Milestone | Kill-Switch Threshold |
| :--- | :---: | :--- | :--- | :--- |
| **Gate 0: Discovery & Data Audit** | 10% | Data audit, architecture design, compliance review | Clean data pipeline & technical sign-off | Data quality score $< 70\%$ |
| **Gate 1: Seed / POC** | 20% | Baseline model setup, benchmark harness, prototype UI | Accuracy & latency benchmark validation | Model accuracy $< 75\%$ after 2 iterations |
| **Gate 2: Pilot & Growth** | 40% | Microservice integration, pilot deployment, HITL feedback | Live pilot adoption & business KPI improvement | User adoption $< 50\%$ or error rate $> 5\%$ |
| **Gate 3: Scale & Transform** | 30% | Full production rollout, automated STP, enterprise scale | Target r-ROI realization & enterprise adoption | Cost overrun $> 30\%$ without ROI lift |

---

## 5. Sensitivity Analysis Framework

Always evaluate financial returns across 3 risk scenarios:

1. **Conservative Case ($P_s - 15\%$, Benefits $-20\%$)**: Lower adoption, higher latency, additional fine-tuning required.
2. **Base Case ($P_s$, Baseline Benefits)**: Target feasibility score and expected throughput gains.
3. **Aggressive Case ($P_s + 10\%$, Benefits $+20\%$)**: Rapid user adoption, higher straight-through processing (% STP).
