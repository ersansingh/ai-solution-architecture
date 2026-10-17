# Enterprise AI Strategy, Feasibility & Risk-Adjusted Business Roadmap

> **Industry / Domain**: Finance Operations / Accounts Payable (cross-industry, ERP-integrated)
> **Problem Statement Ref**: Automated Invoice-to-Purchase-Order Reconciliation and Anomaly Detection (BRD: `InvoiceReconcilation.md`)
> **Target Audience**: CFO / Finance Controller / Chief AI Officer / Investment Committee / Internal Audit

---

## Assumptions (stated because the BRD gives no financial or volume data)

The BRD deliberately leaves numerical targets "to be agreed with the business". The figures below are **planning baselines, not facts**. Replace them at Gate 0 with measured values.

| Assumption | Value | Basis |
| :--- | :---: | :--- |
| Invoice volume | 6,000 / month (72,000 / year) | Mid-size enterprise AP function |
| Annual invoiced spend | $60M | Assumed |
| Manual cost per invoice (match, validate, chase) | $8.00 | ~12 min x $40/hr loaded rate |
| Target cost per invoice (AI + human review of exceptions) | $2.50 | 65% STP; remainder reviewed by humans |
| Billing leakage (duplicates, price/qty overbilling) | 0.5% of spend = $300,000 | Industry-typical range 0.5-1% |
| Share of leakage caught by the system | 50% | Duplicate and price/qty checks |
| Benefit horizon | 12-month **steady-state run-rate** | Ramp-up not modeled; see sensitivity |

---

## STEP 1: Executive Stakeholder Decision Card & Business Alignment

### Executive Decision Card

| Metric / Decision Point | Value / Recommendation | Strategic Rationale |
| :--- | :--- | :--- |
| **Funding Recommendation** | **APPROVE GATE 0 + GATE 1 SEED FUNDING ($72,000)** | Validate real document quality, ERP/PO data access and extraction accuracy before committing the balance |
| **Total 12-Month Investment (TCO)** | `$240,000` | Capex $180,000 + Opex $60,000 |
| **Expected Annual Benefits** | `$600,000` | Labor $396,000 + leakage prevention $150,000 + discount capture/audit effort $54,000 |
| **Unadjusted ROI** | `150%` | $\frac{600{,}000 - 240{,}000}{240{,}000} \times 100\%$ |
| **Probability of Success ($P_s$)** | `68%` | Weighted feasibility 6.8 / 10 |
| **Risk-Adjusted ROI (r-ROI)** | **`70%`** | $\frac{408{,}000 - 240{,}000}{240{,}000} \times 100\%$ |
| **Expected Monetary Value (EMV)** | **`$187,200`** | $(0.68 \times 360{,}000) - (0.32 \times 180{,}000)$ |
| **Payback Period** | `4.8 months` | $\frac{240{,}000}{600{,}000 / 12}$ (steady-state run-rate) |
| **Time-to-First-Value** | `4 months` | Pilot on one supplier segment, shadow mode |

### Strategic Alignment
1. **Financial Control & Leakage Reduction**: Systematic detection of duplicate invoices, repeated billing and price/quantity overbilling that manual sampling misses.
2. **Operational Excellence**: Cuts cost and cycle time per invoice, so AP staff move from keying and matching to resolving real exceptions.
3. **Audit & Compliance Readiness**: Every decision carries evidence, rule version and source-document links (BR-11), which supports SOX-style controls and shortens audit preparation.

### Current State vs. Desired AI-Enabled Future State
* **Current State**: Invoices and POs arrive as digital PDFs, scans and images. AP staff re-key data, locate the PO by hand and compare lines, prices and totals. Duplicates are caught only by memory or sampling. Decisions are inconsistent and the audit trail is thin.
* **Desired AI-Enabled Future State**: The system discovers documents in authorized Google Drive folders, classifies and extracts them, validates the fields, identifies the PO, reconciles lines and totals under approved tolerances, and writes a traceable result through the existing backend API. Only clean, fully-passing cases auto-reconcile. Ambiguous, suspicious or low-confidence cases go to the exception process. The system **never** pays, posts to the ledger or declares fraud.

---

## STEP 2: Opportunity & Multi-Factor Feasibility Scoring

### Why Now & Why This?
* **High Operational Friction**: Mixed-format documents (scanned PDFs, JPEG/PNG) make rule-only or template-OCR tools brittle, and manual matching does not scale with invoice volume.
* **Financial Exposure**: Duplicate and over-billing leakage is direct, recoverable cash that is only partly visible today.
* **Technological Readiness**: Managed document-AI and multimodal LLMs now extract invoice fields reliably, with per-field confidence scores. Deterministic code can then do the reconciliation math, so the model never decides money outcomes.

### Multi-Factor Feasibility Assessment

| Feasibility Pillar | Score (1-10) | Evaluation & Key Drivers |
| :--- | :---: | :--- |
| **Technical Feasibility** (30%) | `8 / 10` | Commodity document extraction plus deterministic matching rules. Fuzzy line-item matching and anomaly scoring add moderate complexity. |
| **Data Feasibility** (30%) | `6 / 10` | Scan quality varies. PO master data, "remaining quantity" and invoice history must come from an authoritative system. No labeled ground-truth set exists yet. |
| **Operational Feasibility** (20%) | `7 / 10` | Fits an existing AP workflow and backend API (frontend out of scope). Needs tolerance policies and an exception process signed off by Finance and Procurement. |
| **Regulatory & Compliance** (20%) | `6 / 10` | Financial records need a full audit trail, retention rules and access control (SOX, GDPR for supplier contacts). Advisory only, with no autonomous payment, so risk is moderate. |
| **Weighted Overall Feasibility** | **`6.8 / 10`** | $(0.3 \times 8) + (0.3 \times 6) + (0.2 \times 7) + (0.2 \times 6) = 6.8$ → **$P_s = 68\%$** |

### Value vs. Feasibility Matrix Positioning
* **Categorization**: **High Value / Medium-High Feasibility (Priority 1, staged "Prove-then-Scale")**
* **Strategic Rationale**: The return is large and measurable, and the main uncertainties (data readiness, the 15 policy decisions in BRD section 15) are cheap to resolve early. That favors small seed funding with gated scale-up over a single large commitment.

---

## STEP 3: Financial Scoping, Risk-Adjusted Metrics & Funding Gates

### Operational Boundaries
* **In-Scope**:
  1. Discovery, classification and extraction of invoices, POs and credit notes from authorized Google Drive folders (PDF, scanned PDF, JPEG/PNG).
  2. Validation, PO identification and line-item / financial reconciliation under approved tolerances.
  3. Anomaly detection (duplicates, repeated billing, price/quantity/tax/total/currency/supplier discrepancies) with explanations.
  4. Traceable result storage, exception routing, idempotent reprocessing and exposure through the existing backend API.
* **Out-of-Scope (Phase 1 Boundaries)**:
  1. Payments, bank transfers, ledger postings or payment approval; creating or amending POs; any fraud determination.
  2. Frontend screens, new file formats, and changes to the existing API contract without approval.

### Detailed 12-Month Financial Model & Risk-Adjusted Return

```
TCO                    = Capex + Opex                       = 180,000 + 60,000 = 240,000
Net Benefits (NB)      = B - TCO                            = 600,000 - 240,000 = 360,000
ROI                    = NB / TCO                           = 150%
Payback                = TCO / (B / 12)                     = 4.8 months
Risk-Adjusted Benefits = B x Ps                             = 600,000 x 0.68 = 408,000
r-ROI                  = (Br - TCO) / TCO                   = 168,000 / 240,000 = 70%
EMV                    = Ps x NB - (1 - Ps) x Capex         = 244,800 - 57,600 = 187,200
```

| Financial Category | Baseline Projection | Risk-Adjusted Projection | Notes & Calculation Basis |
| :--- | :---: | :---: | :--- |
| **Upfront Setup & Engineering (Capex)** | `$180,000` | `$180,000` | Architecture and security design $30k; Drive/ERP integration and ingestion $40k; extraction and matching engine $55k; anomaly rules and evidence store $30k; golden test set and labeling $25k |
| **Annual Infrastructure & Operations (Opex)** | `$60,000` | `$60,000` | Document-AI/LLM API $22k; cloud hosting and storage $14k; MLOps, monitoring and support $24k |
| **Total 12-Month Investment (TCO)** | **`$240,000`** | **`$240,000`** | Capex + 1 year Opex |
| **Total 12-Month Expected Benefits** | `$600,000` | `$408,000` | Baseline x $P_s$ (68%) |
| **Net Financial Value (Net Benefits)** | `$360,000` | `$168,000` | Benefits - TCO |
| **ROI / r-ROI** | **`150%`** | **`70%`** | Baseline vs. risk-adjusted |
| **Expected Monetary Value (EMV)** | N/A | **`$187,200`** | Downside capital = Capex $180,000 |
| **Payback Period** | `4.8 months` | `7.1 months` | Risk-adjusted: $240{,}000 / (408{,}000 / 12)$ |

**Benefit build-up (baseline)**

| Benefit | Calculation | Annual Value |
| :--- | :--- | :---: |
| Labor efficiency | 72,000 invoices x ($8.00 - $2.50) | `$396,000` |
| Duplicate / over-billing prevention | $300,000 leakage x 50% caught | `$150,000` |
| Early-payment discount capture and reduced audit prep | Faster cycle time, evidence on demand | `$54,000` |
| **Total** | | **`$600,000`** |

### Sensitivity Analysis

| Scenario | $P_s$ | Benefits | Net Benefits | r-ROI | EMV |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Conservative ($P_s$ -15 pts, benefits -20%) | 53% | $480,000 | $240,000 | `6%` | `$42,600` |
| **Base** | **68%** | **$600,000** | **$360,000** | **`70%`** | **`$187,200`** |
| Aggressive ($P_s$ +10 pts, benefits +20%) | 78% | $720,000 | $480,000 | `134%` | `$334,800` |

The conservative case still breaks even, so the investment is robust to the assumptions. It is most sensitive to the **STP rate** and **leakage rate**, which Gate 0 should measure.

### Stage-Gate Capital Release Schedule

| Gate Horizon | Phase / Tranche | Capital Allocation (%) | Dollar Amount ($) | Gate Release Milestone & Kill-Switch Criteria |
| :--- | :--- | :---: | :---: | :--- |
| **Gate 0** | **Discovery & Data Audit** | `10%` | `$24,000` | **Milestone**: Sample of >= 500 real invoices/POs profiled; ERP/PO data access and Drive permissions confirmed; BRD section 15 decisions scheduled (tolerances, matching IDs, duplicate policy).<br>**Kill Switch**: Data quality score < 70%, or no authoritative PO/remaining-quantity source available. |
| **Gate 1** | **Seed / POC** | `20%` | `$48,000` | **Milestone**: On the golden set, critical-field extraction accuracy >= 95%, correct PO identification >= 95%, and zero unsafe auto-approvals.<br>**Kill Switch**: Critical-field accuracy < 85% after 2 tuning sprints. |
| **Gate 2** | **Pilot & Integration** | `40%` | `$96,000` | **Milestone**: Shadow-mode pilot on one supplier segment; backend API integration live; exception routing and audit evidence working.<br>**Kill Switch**: Reviewer overrides > 15%, or any confirmed false auto-reconciliation of a non-compliant invoice. |
| **Gate 3** | **Scale & Automation** | `30%` | `$72,000` | **Milestone**: All approved suppliers on-boarded; STP >= 60%; leakage detection measured against baseline.<br>**Kill Switch**: Cost overrun > 30%, or STP < 40% with no improvement trend. |

---

## STEP 4: Comprehensive AI Risk Profile & Mitigation Plan

| Risk Category | Risk Event / Failure Mode | Impact | Probability | Mitigation Strategy | Residual Risk |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **Technical & Model** | Wrong extraction of amounts, quantities or PO number on poor scans | High | Medium | Per-field confidence thresholds; critical fields below threshold go to review (never guessed, per BRD 6.3); arithmetic cross-checks (lines vs. total) | Low |
| **Technical & Model** | LLM "invents" a missing value or picks a PO arbitrarily among candidates | High | Low | LLM only extracts; deterministic code reconciles; ambiguous multi-PO match always routed to review (BRD 8.1) | Low |
| **Financial Control** | False auto-reconciliation lets an erroneous invoice pass | High | Low | Auto-reconcile only when **all** mandatory checks pass (BRD 11); golden-set regression gate; no payment or ledger action by design | Low |
| **Financial Control** | Duplicate or partial invoicing logic (partial invoices, credit notes, multiple invoices per PO) is under-defined | High | Medium | Resolve in Gate 0 (BRD section 15); default unresolved cases to "Requires review" | Medium |
| **Data & Governance** | Exposure of supplier/bank/PII data or over-broad Drive access | High | Low | Least-privilege service account on named folders only; encryption in transit/at rest; no-retention model endpoints; access logging | Low |
| **Data & Governance** | PO master data stale or unavailable, so remaining quantities are wrong | High | Medium | Gate 0 kill-switch on authoritative source; data freshness checks; mark result "Requires review" if stale | Medium |
| **Compliance & Audit** | Decision cannot be reproduced for auditors after a rule change | Medium | Medium | Store rule/policy version, extracted values, variances and timestamps per decision; immutable audit records | Low |
| **Operational & Adoption** | AP staff distrust results or are flooded by false-positive exceptions | Medium | Medium | Shadow mode first; tunable tolerances; explanations on every anomaly; track override rate | Low |
| **Operational** | Reprocessing creates duplicate records or repeated effects | Medium | Medium | Idempotency keys on document hash plus rule version (BR-10, BR-13); safe-retry testing | Low |
| **Financial & Vendor** | API/token cost growth or vendor outage | Medium | Medium | Monthly budget caps, caching, fallback extractor, retry with backoff and dead-letter queue | Low |

---

## STEP 5: End-to-End Phased AI Project Roadmap

| Workstream | Phase 1: Foundation (0-3M) | Phase 2: Pilot (3-6M) | Phase 3: Scale (6-12M) | Phase 4: Transform (12+M) |
| :--- | :--- | :--- | :--- | :--- |
| **Data & Infrastructure** | Profile sample documents; secure Drive access; confirm PO/ERP data source; set up evidence store and idempotent ingestion | Production pipeline, retries and dead-letter handling, monitoring | Multi-folder, multi-entity ingestion; retention and audit-archive policies | Near-real-time ingestion; cross-entity supplier master |
| **Model Development** | Extraction benchmark; golden test set; classification of invoice / PO / credit note | Line-item matching, tolerance engine, duplicate and repeated-billing detection | Anomaly scoring tuned on reviewer feedback; multi-currency and tax-rule support (if approved) | Continuous learning from overrides; supplier-specific tuning |
| **Integration & STP** | API gap analysis against existing contract; outcome and status model agreed | Result publication via backend API; exception routing; shadow-mode run | Auto-reconcile of fully-passing invoices; downstream system consumption | Wider STP; optional ERP hand-offs (separately authorized) |
| **Change Management** | Stakeholder sign-off on section 15 decisions; define exception process | Train AP reviewers; feedback loop in shadow mode | Roll out by supplier segment; update SOPs | AI literacy; continuous policy review |
| **Value Realization** | Baseline cost per invoice, cycle time, leakage; Gate 0 and 1 audit | Pilot KPIs vs. baseline; Gate 2 review | Gate 3 benefits report; leakage recovered | Long-term r-ROI audit; extend to other three-way-match scenarios |

---

## STEP 6: Govern, Measure & Adapt (Ensure Value Realization)

### Critical Business & Technical KPIs

#### 1. Financial & Business Impact KPIs
* **Cost per invoice**: from `$8.00` to `$2.50` (69% reduction).
* **Leakage prevented**: `>= $150,000` in year 1 (duplicates and over-billing caught before payment).
* **Net benefit**: `$360,000` baseline / `$168,000` risk-adjusted in year 1.

#### 2. Operational Efficiency KPIs
* **Turnaround time**: from days to `< 1 hour` for system processing; exceptions triaged the same day.
* **Straight-through processing (STP) rate**: `>= 60-65%` of invoices auto-reconciled with all mandatory checks passed.
* **Duplicate-record rate from reprocessing**: `0`.

#### 3. AI Performance & Quality KPIs
* **Critical-field extraction accuracy**: `>= 95%` on the golden set.
* **Correct PO identification**: `>= 95%`; ambiguous cases flagged, never guessed.
* **Unsafe auto-approval rate**: `0` on the regression suite and monitored in production.
* **Hallucinated / invented field values**: `0`; missing fields explicitly flagged.
* **Processing latency (p95)**: agree at Gate 0 (BRD requires targets agreed, not invented).

#### 4. User Experience & Adoption KPIs
* **Reviewer override rate**: `< 15%` and trending down.
* **Exception queue age**: `< 2 business days` median.
* **AP reviewer trust score**: `>= 4 / 5` in pilot survey.

### Governance Structure & Steering Cadence
1. **Executive Steering Committee** (Finance Controller, CFO delegate, Procurement, IT, Information Security): monthly. Reviews r-ROI and approves stage-gate releases and BRD section 15 policy decisions.
2. **Cross-Functional Delivery Squad** (Product Owner, AI/ML and backend engineers, AP SMEs): weekly sprints.
3. **Audit & Control Review** (Internal Audit, Information Security): bi-weekly in pilot, then quarterly. Covers evidence quality, access logs, rule-version changes and model drift.

### Kill-Switch Triggers (pause capital or pivot)
* Data quality score < 70% at Gate 0, or no authoritative PO source.
* Critical-field accuracy < 85% after 2 tuning sprints (Gate 1).
* Any confirmed false auto-reconciliation of a non-compliant invoice: stop auto-reconcile and revert to review-only until root cause is fixed.
* Reviewer override rate > 15% after pilot tuning, or STP < 40% at Gate 3.
* Cost overrun > 30% without matching benefit lift.
* Pivot options: swap the extractor, narrow to digital PDFs only, or run in recommend-only mode.

### Decisions Needed Before Gate 1 (from BRD section 15)
Matching identifiers, quantity/price/total tolerances, partial invoicing and multiple-invoice rules, duplicate-detection policy, credit-note and cancelled-PO handling, currency policy, exception routing and auto-reconcile eligibility. These sit on the critical path, because without them the "Matched within tolerance" and "Requires review" boundaries cannot be tested.
