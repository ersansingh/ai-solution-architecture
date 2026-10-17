# AI Algorithm & Model Recommendation Report: Automated Invoice-to-PO Reconciliation and Anomaly Detection

> **Source problem statement**: `lab-ai-algorithm-selection/invoice-reconcililation/InvoiceReconcilation.md`
> **Companion document**: `lab-ai-algorithm-selection/invoice-reconcililation/InvoiceReconcilation_Strategy_Roadmap.md`

---

## 1. Executive Summary

The BRD asks for an automated pipeline that discovers invoices and POs in Google Drive (digital PDF, scanned PDF, JPEG/PNG), extracts their data, matches each invoice to a PO, reconciles lines and totals under approved tolerances, flags anomalies, and stores traceable results. It must never pay, post to the ledger, or declare fraud, and it must never auto-approve ambiguous or unsafe cases.

**Recommendation: a hybrid architecture in which ML is used only where the input is genuinely unstructured, and deterministic logic makes every financial decision.**

1. **Extraction (the ML core)**: layout-aware document AI plus a multimodal LLM that returns schema-constrained JSON with per-field confidence. A fine-tuned LayoutLMv3 is the self-hosted alternative.
2. **Matching and reconciliation**: a deterministic rules engine for PO lookup, currency, quantity, price, tax and total checks, using decimal arithmetic and a versioned tolerance policy. Fuzzy line matching uses embeddings with the Hungarian algorithm only for lines that lack a shared identifier.
3. **Anomaly detection**: hash and fuzzy-key duplicate detection, plus rule-based checks. A supervised LightGBM / unsupervised Isolation Forest risk score is added in a later phase as a *review-prioritization signal only*.

Expected performance after tuning on a golden set: critical-field extraction >= 95%, correct PO identification >= 95%, zero unsafe auto-approvals. **Confidence: Medium-High.** The technology is mature, but the policy decisions in BRD section 15 and the availability of an authoritative PO source are open.

---

## 2. Business Problem Analysis

* **Business Objective**: Automate invoice-to-PO reconciliation with traceable evidence, cutting manual effort and catching duplicate or over-billing.
* **Current Process**: AP staff read mixed-format documents, re-key data, find the PO, and compare lines, prices and totals by hand. Duplicates are caught by memory or sampling.
* **Pain Points**: Missing or wrong PO references; quantity, price, tax and total errors; duplicates and repeated billing; poor scans; inconsistent decisions; weak audit trail.
* **Expected Outcome**: Fully-passing invoices auto-reconciled (target 60-65% STP); all others routed to an exception process with explanations; every decision reproducible.
* **Success Criteria**:
  * *Business*: lower cost and cycle time per invoice; leakage prevented.
  * *Technical*: critical-field accuracy >= 95%; PO identification >= 95%; 0 unsafe auto-approvals; idempotent reprocessing; results available via the existing API.
* **Stakeholders**: Finance/AP (tolerances), Procurement (PO validity), Finance Controller (controls), IT/Engineering, Information Security, Internal Audit, Business Owner.
* **Constraints**: Frontend excluded; existing API contract fixed; no payments/postings; missing fields must be flagged, never invented; tolerances, retention and SLAs are not yet defined.

---

## 3. AI Suitability Assessment

* **Alternatives Considered**:
  * *Business rules / SQL*: ideal for the **comparison** step (PO match, quantity, price, tax, totals, currency, eligibility). They are exact, auditable and deterministic.
  * *Template OCR / RPA*: works only for fixed supplier layouts and breaks on new formats and poor scans.
  * *RAG*: not applicable. The task is structured extraction and comparison, not knowledge retrieval.
  * *Mathematical optimization*: only a small assignment problem (line-to-line matching), solved with the Hungarian algorithm.
  * *Traditional software engineering*: required for idempotency, evidence storage, API and exception routing.
* **Why ML Is Recommended (narrowly)**: Reading scanned and varied documents into structured fields is unstructured-data perception, which rules cannot do at acceptable accuracy across suppliers. A learned model also helps with document classification (invoice / PO / credit note) and fuzzy line-description matching.
* **Why ML Is NOT Recommended for the decision itself**: Reconciliation outcomes involve money and need explainable, versioned, reproducible logic (BR-09, BR-11). The BRD also bars automatic fraud determination. Models therefore **propose and score**, while **rules decide**.

---

## 4. Problem Classification

* **ML Task Category**: (a) Document classification; (b) Document Intelligence / key-information and table extraction (NLP + vision); (c) Entity resolution (PO, supplier, duplicates); (d) Fuzzy line-item matching (assignment); (e) Anomaly detection / risk scoring (secondary).
* **Data Modality**: Multi-modal unstructured documents (digital PDF, scanned PDF, JPEG/PNG) plus structured PO/ERP records.
* **Learning Paradigm**: Hybrid: pre-trained foundation/document models used zero-shot or lightly fine-tuned (transfer learning), combined with deterministic rules; optional supervised/unsupervised anomaly scoring later.
* **Execution Mode**: Event-driven / near-real-time micro-batch on new Drive files, with scheduled batch reprocessing. No sub-second requirement is stated.
* **Classification Reasoning**: Each stage has a different best tool, so a single model type would be a poor fit: perception for pages, rules for finance, and statistics for rare-event scoring.

---

## 5. Data Assessment

### Data Type
* Unstructured documents (PDF, scans, images) and structured PO/ERP data (assumed available through an authoritative system).

### Data Quality (assumptions, to be verified at Gate 0)
* **Dataset Size**: ~72,000 invoices / year (6,000 / month); PO volume comparable; document size and page limits not yet defined.
* **Features**: Header fields (~12), line items (variable, ~5 fields each), plus table structure and page layout; embeddings for line descriptions.
* **Label Availability**: No labeled extraction ground truth exists today. A golden set of ~500-1,000 human-verified documents must be created. Historical reconciled invoices may supply weak labels.
* **Missing Values**: Moderate on scans; some fields (PO number, due date) legitimately absent. Missing must be preserved as "unavailable".
* **Class Imbalance**: Severely imbalanced for anomalies (likely < 1-3% true duplicates or over-billing), so supervised anomaly labels will be sparse.
* **Outliers**: Rotated, skewed, low-resolution, handwritten and multi-language documents; unusual tax or currency formats.
* **Historical Depth**: Unknown; assume 12-24 months of archived invoices for tuning and duplicate baselines.
* **Overall Data Quality**: Medium. Document variety and unlabeled data are the main risks. The PO master (status, remaining quantity) is the critical dependency.

---

## 6. Recommended Learning Paradigm

* **Selected Paradigm**: **Hybrid AI**: transfer learning / foundation models for extraction and classification, deterministic rules for reconciliation, and optional unsupervised/supervised scoring for review prioritization.
* **Justification**: Pre-trained document models need little labeled data and handle layout variety. Rules supply the auditability and zero-tolerance for invented values that the BRD demands. Anomaly learning is deferred because labels are scarce and the BRD warns that anomalies are not proof of fraud.
* **Alternatives Considered**: Training a document model from scratch (needs far more labels, no benefit). A purely LLM-driven end-to-end reconciler (non-deterministic, hard to audit, risk of arbitrary PO selection). Pure RPA/templates (brittle).

---

## 7. Top Three Algorithms

The ranking below is for the **extraction component**, the one place ML is the core. Supporting algorithms for the other stages follow.

### Rank 1 (Recommended): Managed Document AI + Multimodal LLM Structured Extraction
* **Model Category**: OCR/layout analysis service + vision-language foundation model with schema-constrained (JSON) output
* **Specific Implementation**: A managed invoice-extraction service (e.g. Amazon Textract AnalyzeExpense or Azure Document Intelligence prebuilt-invoice) for OCR, key-values and tables, plus a multimodal LLM (e.g. a Claude model on Amazon Bedrock, or Qwen2-VL for self-hosting) as a verifier and fallback for low-confidence fields and hard layouts
* **Why Recommended**:
  * Strong out-of-the-box accuracy on invoices and POs across suppliers, with no large labeled set required to start.
  * Provides per-field confidence and bounding-box provenance, which feed the "unreliable critical field means review" rule and the audit trail (source reference).
  * Fastest path to value and managed scaling; cost per page is low relative to the $8 manual cost. The LLM is limited to extraction and **cannot** pick a PO or approve anything.

### Rank 2 (Alternative): Fine-tuned LayoutLMv3 (or Donut) on the Golden Set
* **Model Category**: Layout-aware multimodal Transformer encoder (token classification + table structure)
* **Why Alternative**:
  * Switch if data residency/cost rules out managed APIs, or if volume is high enough that self-hosting is cheaper, or if accuracy on a few dominant suppliers needs further gains.
  * Trade-off: needs 500-2,000+ labeled documents, GPU training and serving, and more MLOps than Rank 1.

### Rank 3 (Baseline): Tesseract/PaddleOCR + Regex & Template Rules
* **Model Category**: Classical OCR with rule-based field parsing
* **Purpose**: Performance floor for the Gate 1 benchmark, a cheap fallback for known fixed-layout suppliers, and a sanity check that justifies the cost of Rank 1/2.

### Supporting Algorithms (non-extraction stages)

| Stage | Recommended Approach | Rationale |
| :--- | :--- | :--- |
| Document classification (invoice / PO / credit note / other) | Layout/Text classifier (LayoutLMv3 head or LLM zero-shot with confidence) with rule override on keywords | Few classes; rules give cheap sanity checks |
| PO identification | Deterministic lookup on normalized PO number, then supplier + date + amount candidate retrieval; **no arbitrary choice when > 1 plausible** | Required by BRD 8.1 |
| Supplier identity | Normalization + Jaro-Winkler / token-set fuzzy match against supplier master, tax-ID exact match when present | Explainable; names vary across documents |
| Line-item matching | Match by item ID first; otherwise sentence-embedding similarity (BGE / E5) + Hungarian assignment with a minimum-score threshold | Handles description variance; unmatched lines stay unmatched |
| Financial reconciliation | Rules engine with `Decimal` arithmetic, tolerance policy and rounding rules, versioned | Exact, auditable, reproducible |
| Duplicate / repeated-billing detection | File hash, normalized (supplier, invoice no., date, amount) key, plus blocking + fuzzy match; cumulative billed-quantity check per PO line | Deterministic and explainable |
| Risk scoring (Phase 3+) | Isolation Forest (unsupervised) first; LightGBM once reviewer-confirmed labels accumulate | Prioritizes review queue; never a decision or fraud verdict |

---

## 8. Algorithm Comparison Table

| Evaluation Dimension | Rank 3 Baseline (OCR + Regex/Template) | Rank 1 Recommended (Managed Doc AI + Multimodal LLM) | Rank 2 Alternative (Fine-tuned LayoutLMv3) |
| :--- | :--- | :--- | :--- |
| **Business Fit** | Low-Medium | High | High |
| **Data Suitability** | Low (fails on varied/scanned docs) | High (no labeled set to start) | High (needs golden set) |
| **Expected Accuracy** | ~60-75% critical fields | ~93-97% critical fields (after validation rules) | ~95-98% on trained suppliers/layouts |
| **Interpretability** | High (explicit rules) | Medium (confidence + bounding boxes) | Medium (token labels + boxes) |
| **Scalability** | High | High (managed) | Medium-High (own GPU fleet) |
| **Training Time** | None | None / prompt-schema design only | Moderate (hours-days per run) |
| **Inference Latency** | < 2 s / page | ~2-8 s / page (LLM fallback adds time) | ~0.5-2 s / page on GPU |
| **Computational Cost** | $ | $$ (per-page API fees) | $$-$$$ (GPU hosting + labeling) |
| **Hyperparameter Complexity** | Low | Low (thresholds, prompts) | Medium-High |
| **Production Readiness** | Medium | High | Medium |

Accuracy figures are planning estimates, not measurements. Gate 1 benchmarks on the golden set will replace them.

---

## 9. Feature Engineering Recommendations

1. **Missing Value Handling**: Never impute financial or identifier fields. Store `null` with a reason code (`not_present`, `low_confidence`, `unreadable`) and route to review when a critical field is affected. Imputation is allowed only in the optional risk model.
2. **Encoding**: Normalize supplier IDs, PO numbers (strip separators, case, leading zeros), currency codes (ISO 4217), and unit-of-measure codes. Frequency/target encoding only in the optional risk model.
3. **Scaling & Normalization**: Parse amounts with locale-aware rules (decimal and thousands separators), store as `Decimal` in minor units. Robust scaling only for the risk model.
4. **Feature Selection**: SHAP-based pruning for the risk model; for extraction, keep only fields in the approved schema (BRD 6.2 / 6.3).
5. **Feature Creation**: Line-total check (qty x unit price - discount), subtotal-vs-sum-of-lines delta, tax-rate-implied vs stated tax, invoice-vs-PO price ratio, cumulative billed vs ordered quantity, days between PO and invoice date, supplier historical dispute rate, invoice amount z-score per supplier.
6. **Outlier Handling**: Flag, don't clip, since outliers are the signal. Winsorize only for risk-model training.
7. **Class Balancing**: For the supervised risk model use class weights / `scale_pos_weight` and PR-AUC threshold tuning. Avoid SMOTE on financial records.
8. **Data Augmentation**: For fine-tuning, synthetic degradation of scans (rotation, blur, noise, JPEG compression, low DPI) and layout/font variation.
9. **Domain-Specific Processing**: Pre-processing for scans (deskew, denoise, DPI normalization, orientation fix), multi-page PDF handling, document hash for idempotency, embedding generation for line descriptions, multilingual handling if suppliers require it.

---

## 10. Evaluation Metrics

* **Primary Optimization Metric**: Field-level exact-match accuracy on **critical fields** (invoice no., supplier, PO no., currency, totals, tax, line qty/price), plus an **unsafe auto-approval rate** target of 0.
* **Secondary Metrics**:
  * *Extraction*: field F1, table/line-item F1, word/character error rate, confidence calibration (ECE), percentage of documents routed to review.
  * *Classification*: macro-F1 and confusion matrix (invoice vs credit note is high-stakes).
  * *Matching*: PO identification accuracy, ambiguous-case recall (must be flagged), line-match precision/recall.
  * *Anomaly*: precision and recall by category, false-positive rate, Precision@K for the review queue (PR-AUC if supervised).
  * *System*: STP rate, reviewer override rate, p95 latency per document, cost per document.
* **Cross-Validation Strategy**: Group K-Fold by **supplier** (to test generalization to unseen layouts) and a temporal hold-out for the risk model. Maintain a frozen regression golden set with known edge cases (partial invoices, credit notes, multi-PO candidates, currency mismatch, rounding).
* **Hyperparameter Tuning Framework**: Optuna for confidence thresholds, matching similarity cut-offs and risk-model parameters. Tolerances are **business policy** and are set by Finance, not tuned by optimization.

---

## 11. Production Architecture & MLOps

* **Inference Mode**: Event-driven near-real-time per file, with scheduled batch sweeps and manual or rule-update reprocessing.
* **Training Mode**: Offline. Managed extraction needs no training; LayoutLMv3 and the risk model are retrained offline from reviewer-corrected data.
* **Pipeline Pattern**: Drive Watcher (changes API / scheduled scan) to queue (SQS / Pub/Sub) to idempotent workers (key = document hash + rule version) to extraction to validation to PO match to reconciliation rules to anomaly checks to result store and evidence to API / exception queue. A dead-letter queue and retries with backoff handle failures (BR-13).
* **Feature Store**: Not needed initially. If the risk model is built, Feast or a SageMaker/Databricks feature store over supplier and PO history.
* **Model Registry**: MLflow or SageMaker Model Registry (for LayoutLMv3 / risk model); prompt/schema and rule/policy versions kept in Git and recorded on every decision.
* **Experiment Tracking**: MLflow (golden-set runs per model, prompt and threshold version).
* **Model Serving**: Managed API for Rank 1; for Rank 2 serve via KServe / Triton or a SageMaker endpoint. FastAPI service for the reconciliation engine and API.
* **CI/CD Pipeline**: GitHub Actions: unit tests, golden-set regression gate (fails the build on any unsafe auto-approval or accuracy drop), IaC (Terraform), container build, staged deployment.
* **Monitoring & Drift Detection**: Prometheus + Grafana / CloudWatch for throughput, latency, error and queue age; Evidently AI for field-confidence and amount-distribution drift (PSI / KS); alerts on rising review rate, falling confidence, or new supplier layouts.
* **Deployment Strategy**: **Shadow mode first** (results recorded, not acted on), then canary by supplier segment, then enable auto-reconcile only for fully-passing cases.
* **Retraining Strategy**: Drift- or error-triggered, plus a quarterly review. Reviewer corrections feed the golden set and fine-tuning data. Any rule or tolerance change creates a new policy version and can trigger authorized reprocessing.
* **Security & Audit**: Least-privilege Drive service account on named folders, encryption in transit and at rest, no-retention model endpoints, PII redaction in logs, immutable evidence records (source reference, extracted values, comparison results, variances, rule version, timestamps).

---

## 12. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| Extraction error on a critical field (poor scan, odd layout) | Medium | High | Per-field confidence thresholds; cross-checks (line sums vs. subtotal vs. total, tax-rate consistency); critical-field doubt means review, never a guess |
| LLM invents or "repairs" a value, or chooses a PO | Low | High | LLM limited to schema-constrained extraction; values must be traceable to page text/boxes; PO selection in deterministic code; multiple candidates means review |
| False auto-reconciliation (unsafe approval) | Low | High | Auto-reconcile only when all mandatory checks pass; golden-set CI gate; shadow-mode soak; kill-switch back to review-only |
| Data leakage / unrealistic evaluation | Medium | Medium | Group-by-supplier splits; temporal hold-out; preprocessing inside the pipeline |
| Data drift (new suppliers, layouts, scanner quality) | High | Medium | Drift monitoring on confidence and field distributions; new-layout alerts; periodic golden-set refresh |
| Stale or missing PO master data | Medium | High | Freshness checks; "Requires review" when source is unavailable or stale; Gate 0 kill-switch |
| Under-defined business policy (partial invoices, credit notes, tolerances) | High | High | Resolve BRD section 15 before Gate 1; default to review for undefined cases; version all policies |
| Duplicate reprocessing effects | Medium | Medium | Idempotency keys (document hash + rule version); upsert semantics; replay tests |
| Privacy / security (supplier, bank, PII data) | Low | High | Least-privilege access, encryption, no-retention endpoints, PII-safe logging, retention policy per BRD |
| Bias/fairness in supplier risk scoring | Low | Medium | Risk score is advisory only; exclude protected or proxy attributes; review score distribution by supplier segment |
| Adversarial/malicious documents (prompt injection in PDF text) | Low | High | Treat document text as data not instructions; strict output schema; no tool access for the extraction model; validation layer |
| Latency/cost spikes | Medium | Low | Queue-based autoscaling; caching by document hash; LLM only on low-confidence fields; budget alerts |

---

## 13. Implementation Roadmap

| Phase | Activities | Duration |
| :--- | :--- | :--- |
| **1. Business Understanding** | Confirm BRD section 15 decisions (tolerances, matching IDs, duplicate policy, outcomes), KPIs, exception process | 2 weeks |
| **2. Data Collection** | Drive access, sample >= 500-1,000 documents, PO/ERP source and API gap analysis | 2-3 weeks |
| **3. Data Preparation** | Build and label golden set, document-quality profiling, schema and data contracts | 3 weeks |
| **4. Feature Engineering** | Normalizers (PO, supplier, currency, amount), validation features, line-match embeddings | 2 weeks |
| **5. Model Selection** | Benchmark Rank 3 vs Rank 1 vs Rank 2 on the golden set; decide go/no-go (Gate 1) | 2 weeks |
| **6. Training** | Prompt/schema design, optional LayoutLMv3 fine-tune, rules engine and duplicate logic build | 4 weeks |
| **7. Hyperparameter Tuning** | Optuna on confidence and similarity thresholds; tolerance policy plugged in by Finance | 1-2 weeks |
| **8. Evaluation** | Edge-case scenario suite, unsafe-approval testing, explainability and audit-evidence review | 2 weeks |
| **9. Deployment** | Containerized pipeline, CI/CD, API integration, shadow then canary rollout (Gate 2) | 4 weeks |
| **10. Monitoring** | Drift dashboards, alerts, cost and queue monitoring, runbooks | 2 weeks (overlaps 9) |
| **11. Continuous Improvement** | Reviewer-feedback loop, retraining, risk-model (Isolation Forest to LightGBM), new suppliers | Ongoing |

Rough total to pilot: ~5-6 months (matches Phases 1-2 of the strategy roadmap).

---

## 14. Final Recommendation

Build a **hybrid, rules-governed pipeline**: use managed document AI with a multimodal LLM verifier (Rank 1) to extract fields from invoices and POs with confidence and provenance. A deterministic, versioned rules engine makes every PO-match, tolerance and anomaly decision, and anything ambiguous goes to human review. Benchmark against the OCR+regex baseline and a fine-tuned LayoutLMv3 at Gate 1, start in shadow mode, and add Isolation Forest / LightGBM risk scoring only after reviewer-labeled data exists. This delivers the expected STP and leakage-prevention benefits while honoring the BRD's requirement that no unsafe case is automatically approved.

---

## 15. Confidence Level

* **Confidence**: **Medium-High**
* **Reasoning**: Document extraction with layout-aware models is a mature, well-benchmarked capability, and reconciliation is rule-based and deterministic, which keeps the riskiest logic out of the model. Confidence is held below "High" because no real documents, PO data source, or business policies have been seen, and the accuracy figures are estimates until Gate 1.
* **Key Assumptions**:
  * An authoritative PO source with status and remaining quantities is accessible by API or export.
  * Volume is roughly 6,000 invoices per month, with a mix of digital and scanned documents.
  * A golden set of 500-1,000 documents can be labeled by AP staff.
  * Managed cloud AI services are permitted for this data (otherwise use Rank 2, self-hosted).
  * Finance approves tolerances, rounding, duplicate policy and credit-note rules before Gate 1.
