# AI Algorithm & Model Recommendation Report: Enterprise Network Intrusion & Zero-Day Anomaly Detection

> **Paradigm**: Unsupervised Learning (Anomaly & Outlier Detection), evolving to Hybrid Semi-Supervised  
> **Problem Statement**: `lab-ai-algorithm-selection/network-anomaly-detection/network-anomaly-detection.md`  
> **Skill**: `.agents/skills/ai-algorithm-selector/SKILL.md`  
> **Reference Matrix**: `.agents/skills/ai-algorithm-selector/references/algorithm-taxonomy-and-selection-matrix.md`

---

## 1. Executive Summary

A global telecom and enterprise security provider needs to detect zero-day intrusions, unauthorized access, and data exfiltration across a backbone producing **500,000 NetFlow/IPFIX events per second** (~43 billion records, ~2.5 TB per day). The current Snort/Suricata signatures and fixed bandwidth thresholds cannot see novel attacks, and over 90% of their alerts are false positives. There are **no labels for novel attacks**, and the estimated contamination rate is **0.05%–0.1%**. Scoring must take **< 10 ms per flow** on CPU/GPU edge nodes at perimeter routers, and every alert must name the **top 3 contributing features** for SOC analysts.

We recommend a **streaming unsupervised anomaly detection architecture** built on **Isolation Forest** as the primary scoring model. It is trained on a rolling baseline of recent traffic, enriched with **windowed per-entity behavioural features** computed in Apache Flink, exported to **ONNX** and served on **Triton (ONNX Runtime CPU backend)**. Attribution comes from **TreeSHAP / DIFFI path-depth attribution**. To keep inside the latency budget, it is computed asynchronously and only for the ~0.1% of flows that cross the alert threshold. A **shallow Dense Autoencoder** is the alternative and the planned second stage of a score ensemble. It catches the correlated, multi-feature anomalies that axis-parallel trees can miss. A **robust statistical baseline** (per-feature MAD z-scores with EWMA per-entity thresholds) sets the performance floor. As SOC analysts label alerts, the system should become a **hybrid semi-supervised** pipeline: a LightGBM re-ranker trained on analyst decisions and placed on top of the unsupervised score to cut false positives further.

Expected outcome: MTTD falls from 48 hours to **< 30 seconds**, and incident-level alert noise drops by **≥ 65%**. P99 scoring latency should be **~1–3 ms per flow** under micro-batching, well inside the 10 ms SLA. **Confidence: Medium-High.** The algorithm choice is mature and fits the constraints well. The main uncertainty is how well the stated metrics can be measured without labels, and an arithmetic conflict between the Precision@Top-1% target and the stated contamination rate (see Sections 10 and 15).

---

## 2. Business Problem Analysis

* **Business Objective**: Detect novel (zero-day) network threats, intrusions, and data exfiltration in real time without depending on known signatures or historical threat labels, and automate first-line threat isolation for the SOC.
* **Current Process**: Static Snort/Suricata signature rules, fixed bandwidth threshold alerts, manual firewall log review, and forensics after exfiltration has already happened.
* **Pain Points**:
  * Signature systems are blind to polymorphic malware, novel exploit variants, and encrypted command-and-control channels.
  * Over 90% of alerts are false positives, which causes severe analyst fatigue.
  * MTTD for zero-day threats is about 48 hours, so detection happens after the damage.
  * The event volume (500K events/s) is far beyond what people can review.
* **Expected Outcome**: Zero-day detection within 10 seconds of onset; ≥ 65% reduction in false-positive alerts; prevention of high-severity exfiltration; automated first-stage isolation (quarantine VLAN, firewall block recommendations).
* **Success Criteria**:
  * *Business KPIs*: MTTD < 30 s (from 48 h); SOC alert noise reduced ≥ 65%; 99.99% monitoring availability.
  * *Technical KPIs*: Precision@K (top 1% anomaly scores) ≥ 88% on historical audit sets; FPR ≤ 0.5%; < 10 ms streaming scoring latency per flow event; ≥ 500K flow records/s ingestion throughput.
* **Stakeholders**: SOC analysts (Tier 1–3), CISO and security leadership, network operations (NOC), incident response teams, compliance/audit (ISO 27001, SOC 2), and platform/MLOps engineering.
* **Constraints**:
  * **Latency**: < 10 ms per flow, end to end at the scoring service.
  * **Compute**: Edge CPU/GPU nodes at perimeter routers, so models must be small, ONNX-exportable, and deterministic.
  * **Explainability**: Mandatory per-alert top-3 feature attribution in analyst-readable form.
  * **Compliance**: ISO 27001, SOC 2 Type II, and non-intrusive inspection, which means flow metadata only and no payload content retention.
  * **Availability**: 99.99%, so failure must be graceful (fall back to the statistical baseline and existing signatures).

---

## 3. AI Suitability Assessment

* **Alternatives Considered**:
  * **Signature rules (Snort/Suricata)**: Already in place. They work well for *known* threats and should stay as a complementary layer, but by definition they cannot detect zero-days.
  * **Fixed thresholds / business rules**: Single-feature limits (for example, bytes out > X) are what produce today's 90% false-positive rate. They cannot model the joint distribution of 42 interacting features or per-entity baselines.
  * **SQL / BI dashboards**: Useful for retrospective hunting, but not real time and not able to spot multivariate deviations.
  * **Supervised classification (XGBoost on labeled attacks)**: Not viable as the primary approach. There are no labels for novel attacks, and a supervised model learns only the attacks it has already seen, which defeats the zero-day goal.
  * **RAG / Generative AI**: Not suitable for the scoring path (latency of hundreds of ms, cost at 500K events/s). An LLM *could* help later for alert summarization and triage narratives, off the critical path.
  * **Graph analytics**: Valuable for lateral-movement and campaign-level detection, but a later phase, not the core per-flow detector.
* **Why ML Is Recommended**: The task is to model the *normal* multivariate distribution of high-dimensional, non-stationary traffic and flag deviations in it. Rules cannot express this, and labels do not exist for it. Unsupervised density/isolation-based anomaly detection is the standard, proven way to find "unknown unknowns." It turns 500K events/s into a ranked, explainable alert stream that the SOC can act on.
* **Why ML Is NOT Recommended (scope limits)**: ML should **not replace** signature-based IDS for known threats (signatures are cheaper and precise there), and it should **not autonomously enforce** high-impact blocks without a human or a policy gate. Automated isolation should be limited to reversible, low-blast-radius actions at first.

---

## 4. Problem Classification

* **ML Task Category**: Anomaly / Outlier Detection (novelty detection on streaming tabular telemetry), with a secondary ranking task (prioritizing alerts for SOC triage).
* **Data Modality**: Structured tabular time-series / streaming events (NetFlow/IPFIX records with 42 numerical and categorical attributes), with implicit graph structure (source/destination hosts).
* **Learning Paradigm**: Unsupervised Learning (primary), moving to Hybrid Semi-Supervised once analyst feedback labels build up.
* **Execution Mode**: Real-time streaming (Kafka → Flink → Triton) with micro-batched inference at edge nodes; offline daily/rolling retraining.
* **Classification Reasoning**: The target ("significant deviation from baseline behaviour") is defined by distribution, not by labeled classes. Labels for novel attacks are absent by definition, and the 0.05–0.1% contamination rate fits the "rare and different" assumption that isolation- and reconstruction-based detectors rely on. The data is tabular and medium-dimensional (42 features), so tree-based isolation methods are well suited and deep sequence models are not needed for the core detector.

---

## 5. Data Assessment

### Data Type
* Streaming structured telemetry (NetFlow/IPFIX), which is semi-structured at ingestion and normalized to a fixed 42-attribute schema.
* Implicit temporal structure (inter-arrival times, per-host sequences) and graph structure (host-to-host communication).

### Data Quality
* **Dataset Size**: 500K events/s, ~43B records/day, ~2.5 TB/day. Training does not need the full volume; stratified subsamples of 1–10M recent flows per segment are enough for Isolation Forest (the algorithm subsamples 256–4,096 points per tree by design).
* **Features**: 42 NetFlow/IPFIX attributes. These are mostly continuous (flow duration, packet/byte rates, byte ratios, TCP window sizes, SYN/ACK ratios, payload entropy, inter-arrival time statistics), plus categorical/high-cardinality fields (ports, protocols, IPs/ASNs).
* **Label Availability**: Unlabeled. Limited weak labels are available from historical incident audit sets, existing signature hits (known-attack proxies), and red-team exercises.
* **Missing Values**: Assumed low to moderate (< 5%). Missing TCP fields on UDP/ICMP flows are *structurally* missing, not randomly missing, and must be handled per protocol.
* **Class Imbalance**: Severely imbalanced, with an estimated 0.05%–0.1% contamination (1:1,000 to 1:2,000).
* **Outliers**: Benign heavy-tailed outliers are very common (backups, CDN bursts, software updates, scanners run by IT). These are the main source of false positives and must be modeled as normal through per-entity baselines and allow-lists.
* **Historical Depth**: Assumed ≥ 30–90 days of retained flow logs for building baselines and capturing weekly seasonality.
* **Overall Data Quality**: **Medium-High.** Volume and feature richness are excellent and the schema is standardized. Quality is limited by the lack of labels, non-stationarity (concept drift from new services and topology changes), and possible baseline contamination with undetected ongoing attacks.

---

## 6. Recommended Learning Paradigm

* **Selected Paradigm**: **Unsupervised Learning (Anomaly Detection)**, designed to become **Hybrid Semi-Supervised** (unsupervised detector plus a supervised re-ranker trained on analyst feedback).
* **Justification**:
  * Zero-day detection needs a model of *normal*, not a model of *known bad*. Unsupervised methods generalize to attack types that have never been seen.
  * The low contamination rate (≤ 0.1%) makes training on raw production traffic workable for robust methods such as Isolation Forest, with a `contamination` prior to calibrate thresholds.
  * The < 10 ms per-event CPU latency and per-alert explainability requirement favour tree ensembles over deep models (see the latency/explainability spectrum in the reference matrix: Isolation Forest is in the "< 10 ms" tier).
  * The semi-supervised phase uses SOC dispositions (true positive / benign / false positive) to learn site-specific "benign weirdness," which is the main way to reach the ≥ 65% noise reduction target.
* **Alternatives Considered**:
  * **Supervised Learning**: Rejected as primary because there are no labels for novel attacks and it would overfit to known attack families. It is kept for the Phase 2 re-ranker.
  * **Self-Supervised Deep Learning (sequence transformers over flow sequences)**: Rejected for the critical path because of latency, GPU cost at edge nodes, and weak explainability. It could be an offline hunting tool later.
  * **Graph ML (GNNs for lateral movement)**: Deferred to a later phase. It targets campaign-level detection rather than per-flow scoring.
  * **Reinforcement Learning (automated response)**: Rejected. The response policy should be deterministic and auditable for SOC 2 / ISO 27001.

---

## 7. Top Three Algorithms

### Rank 1 (Recommended): Isolation Forest (with Extended Isolation Forest evaluation)
* **Model Category**: Tree-based ensemble isolation anomaly detector.
* **Specific Implementation**: `scikit-learn` `IsolationForest` (200–300 trees, `max_samples` 512–2048, `contamination` ≈ 0.001), exported via `skl2onnx` to ONNX and served on Triton's ONNX Runtime CPU backend. Separate models per traffic segment (for example, per protocol family or per perimeter zone). Benchmark Extended Isolation Forest (`eif`/`isotree`), which removes the axis-parallel scoring artifacts at little cost. Use `isotree` if ONNX export of EIF is not needed.
* **Why Recommended**:
  * **Business fit and data suitability**: Designed for the "few and different" anomaly profile at 0.05–0.1% contamination. It needs no labels, handles mixed-scale continuous features without distance metrics, and is robust to irrelevant features. It is the matrix's primary recommendation for "Unsupervised Tabular Anomaly Detection (Zero Historical Labels)."
  * **Latency and throughput compliance**: Inference is O(trees × log₂(max_samples)), about 2,500 node comparisons per flow, which means microseconds per event on CPU. ONNX Runtime with micro-batches of 256–1,024 flows sustains 500K events/s across a modest edge CPU fleet with P99 well under 10 ms. Training on subsamples takes seconds to minutes, so frequent rolling retrains for drift are cheap.
  * **Explainability and production readiness**: TreeSHAP natively supports `IsolationForest`. DIFFI (Depth-based Isolation Forest Feature Importance) gives cheaper per-sample attribution. Both give the required top-3 features (for example, "SYN/ACK ratio 14σ above host baseline + outbound payload entropy 7.9 bits/byte"). The library is mature and the model is deterministic, small (a few MB), and easy to version and audit.

### Rank 2 (Alternative): Shallow Dense Autoencoder (reconstruction-error detector)
* **Model Category**: Neural reconstruction-based anomaly detector (undercomplete autoencoder; a VAE variant is optional).
* **Specific Implementation**: PyTorch MLP autoencoder (for example, 64→32→12→32→64 over scaled/encoded features), trained on filtered "clean-baseline" traffic, exported to ONNX (INT8 quantized), and served on Triton. The anomaly score is reconstruction error normalized per segment. Per-feature reconstruction error gives the top-3 attribution directly.
* **Why Alternative**:
  * **When to switch / add**: When analyst review or red-team testing shows the Isolation Forest missing *correlated* anomalies, where each feature is individually normal but the combination is not. Examples are low-and-slow exfiltration that mimics normal byte rates with unusual timing/entropy coupling, or protocol tunneling. Autoencoders learn non-linear feature correlations that axis-parallel isolation trees approximate poorly. The recommended end state is a **rank-normalized ensemble (IF + AE)**.
  * **Key trade-off vs Rank 1**: Training is heavier and more sensitive to hyperparameters (architecture, bottleneck size, threshold). It needs a cleaner training baseline because autoencoders can learn to reconstruct contamination. Inference is still fast (~0.5–2 ms per micro-batch on CPU with ONNX INT8), but monitoring and retraining add operational complexity.

### Rank 3 (Baseline): Robust Statistical Baseline (MAD z-scores + per-entity EWMA thresholds)
* **Model Category**: Statistical / rule-based univariate outlier detection.
* **Specific Implementation**: Per-feature robust z-scores (median / MAD) computed against per-entity (host, subnet, service) rolling baselines with exponentially weighted moving averages in Flink. Alert when k features exceed |z| > 4–6.
* **Purpose**: Sets the performance floor and the false-positive benchmark that the ML models must beat, validates the streaming pipeline end to end, and acts as the **fail-safe fallback** if the model-serving tier degrades (to meet the 99.99% availability KPI). The output is fully transparent, and analysts trust it as a sanity check.

*Also evaluated and not ranked*: **Local Outlier Factor**: its kNN-based inference cost and memory footprint are prohibitive at 500K events/s. **One-Class SVM**: O(n²) training, poor scaling to millions of samples, sensitive to kernel/ν tuning. **Deep SVDD**: hypersphere collapse risk, weak explainability, no clear accuracy gain over an AE on 42 tabular features. **HDBSCAN**: useful offline for clustering alerts into campaigns, not for real-time per-flow scoring.

---

## 8. Algorithm Comparison Table

| Evaluation Dimension | Rank 3 Baseline (Robust MAD z-score + EWMA) | Rank 1 Recommended (Isolation Forest) | Rank 2 Alternative (Dense Autoencoder) |
| :--- | :--- | :--- | :--- |
| **Business Fit** | Medium (transparent, but univariate and noisy) | High (zero-day, label-free, explainable) | High (catches correlated / stealthy anomalies) |
| **Data Suitability** | Medium (ignores feature interactions) | High (mixed-scale tabular, low contamination) | High (non-linear correlations; needs a cleaner baseline) |
| **Expected Accuracy** | Precision@K ~40–60%; FPR 1–3% | Precision@K ~80–90%*; FPR ≤ 0.5% | Precision@K ~82–92%*; FPR ≤ 0.5% (higher as ensemble with IF) |
| **Interpretability** | Native (per-feature z-scores) | High (TreeSHAP / DIFFI top-3 features) | Medium-High (per-feature reconstruction error) |
| **Scalability** | High (O(1) streaming state per entity) | High (subsampled training, embarrassingly parallel inference) | Medium-High (GPU helpful for training; CPU inference fine) |
| **Training Time** | Fast (streaming, no training job) | Fast (seconds–minutes on subsamples) | Moderate (tens of minutes–hours per segment) |
| **Inference Latency** | < 0.1 ms | < 1 ms per flow (P99 ~2–3 ms with micro-batch) | ~1–2 ms per flow (ONNX INT8, micro-batch) |
| **Computational Cost** | $ | $ | $$ |
| **Hyperparameter Complexity** | Low (k, z-threshold, EWMA decay) | Low (n_estimators, max_samples, contamination) | High (architecture, bottleneck, learning rate, threshold) |
| **Production Readiness** | High | High (sklearn → ONNX → Triton, mature) | Medium-High (requires stricter drift/retraining governance) |

\* Measured as Precision@K with K sized to the expected anomaly count on labeled audit and red-team sets (see Section 10 on metric definitions).

---

## 9. Feature Engineering Recommendations

1. **Missing Value Handling**: Treat protocol-dependent fields as structurally missing. Impute with a sentinel value plus a binary `is_tcp`/`field_present` indicator instead of the median, so that UDP/ICMP flows are not marked anomalous for missing TCP fields. Segment models by protocol family where distributions differ sharply. Route truly corrupt records (schema violations) to a dead-letter queue, not to the model.
2. **Encoding**: Ports: bucket into well-known / registered / ephemeral ranges, plus frequency encoding of the specific port within the entity's history (rarity = signal). Protocol: one-hot (low cardinality). IPs/ASNs: do **not** encode raw. Replace them with derived features such as internal/external flag, geo/ASN reputation score, and first-seen-recency for the destination.
3. **Scaling & Normalization**: Isolation Forest is scale-invariant per feature, but apply `log1p` to heavy-tailed counters (bytes, packets, duration) for stable SHAP attributions. For the autoencoder, use a `QuantileTransformer` or RobustScaler fitted per segment to blunt heavy tails.
4. **Feature Selection**: Remove near-constant and highly redundant (|ρ| > 0.95) attributes. Use mutual information against weak labels (signature hits, red-team flows) and SHAP-based pruning on the Phase 2 re-ranker. Keep about 25–40 final features to stay inside the latency budget.
5. **Feature Creation (highest-leverage step)**: Compute **windowed per-entity behavioural features** in Flink (10 s / 60 s / 5 min tumbling and sliding windows keyed by source host, destination host, and service). Examples: unique destination ports/IPs contacted (scan detection), outbound/inbound byte ratio, fan-out count, failed-connection (RST/SYN-without-ACK) ratio, deviation from the host's own 7-day hour-of-week baseline, new-destination rate, periodicity/beaconing score (inter-arrival time coefficient of variation), and DNS query entropy where available. Per-flow scoring alone misses multi-flow attacks such as scans, beaconing, and slow exfiltration, so these aggregates are essential.
6. **Outlier Handling**: Do **not** clip outliers in scoring inputs, because outliers are the signal. For *training* sets, remove known-benign heavy hitters (backup servers, CDN, patch distribution) via an allow-list or model them in their own segment, and drop flows that matched signature alerts to reduce baseline contamination.
7. **Class Balancing**: Not applicable to the unsupervised detector. Calibrate the `contamination` prior / threshold to the alert budget instead. For the Phase 2 LightGBM re-ranker, use `scale_pos_weight` and choose the threshold by PR curve.
8. **Data Augmentation**: Inject synthetic attacks (scans, beaconing, exfiltration bursts, SYN floods) generated with red-team tools and public datasets (for example, CIC-IDS2017/2018, UNSW-NB15) into held-out evaluation windows to measure recall on attack types. These are used **only for evaluation and threshold calibration**, never for training the unsupervised baseline.
9. **Domain-Specific Processing**: Use time-of-day and day-of-week encodings (cyclical sin/cos) or time-segmented baselines for diurnal and weekly seasonality. Track per-entity baselines in Feast (online Redis store) with sub-ms lookups. Keep flow-metadata-only inputs to respect non-intrusive inspection: payload entropy must be computed at the sensor as a scalar, without retaining payload content.

---

## 10. Evaluation Metrics

* **Primary Optimization Metric**: **Precision@K** on labeled audit sets and red-team / synthetic-injection windows, together with **FPR** at the operating threshold.
  * *Metric definition caveat*: With a 0.05–0.1% true anomaly rate, the "top 1% of scores" contains 10–20× more flows than there are real anomalies. Precision over the top 1% of *all* traffic is therefore capped at ~5–10%, so the ≥ 88% target is only achievable if **K is sized to the expected anomaly count** (for example, top 0.05–0.1%) or measured on **curated audit sets** with a higher anomaly prevalence. This definition must be agreed with stakeholders in Phase 1.
  * *Operational caveat*: An FPR of 0.5% on 500K flows/s is ~2,500 false-positive *flows per second*. The SOC-facing metric must therefore be measured at the **incident level**, after deduplication and correlation of flow alerts into entity-level incidents over time windows. Otherwise the noise-reduction KPI cannot be met.
* **Secondary Metrics**:
  * PR-AUC and ROC-AUC on audit/red-team sets (threshold-independent model comparison).
  * Recall per attack family (scan, brute-force, C2 beaconing, exfiltration, DoS) on injected attacks, to check zero-day generalization by holding whole families out.
  * Time-to-detect (attack onset → alert) in red-team exercises, against the < 30 s MTTD target.
  * Incident-level SOC metrics: alerts per analyst-hour, analyst-confirmed true-positive rate, noise reduction against the legacy IDS baseline.
  * Systems metrics: P50/P99 scoring latency, throughput (events/s), consumer lag, and service availability.
  * Attribution quality: analyst agreement rating that the top-3 features explain the alert.
* **Cross-Validation Strategy**: **Strict temporal splits** (train on days *t−N…t−1*, evaluate on day *t*) with rolling-origin backtesting across several weeks to capture drift. Attack-family hold-out (leave-one-attack-family-out) to simulate zero-day conditions. No random shuffling across time.
* **Hyperparameter Tuning Framework**: **Optuna**, maximizing Precision@K / PR-AUC on the labeled validation windows under a hard latency constraint (trial rejected if ONNX P99 > 3 ms per micro-batch on the target edge CPU). Search space: `n_estimators`, `max_samples`, `max_features`, segment granularity, and threshold quantile (plus architecture and bottleneck size for the AE).

---

## 11. Production Architecture & MLOps

* **Inference Mode**: Streaming. Perimeter router exporters → **Kafka** (partitioned by source host) → **Flink** (parsing, windowed feature aggregation, Feast online lookups) → **Triton Inference Server** (ONNX Runtime CPU backend, dynamic batching with ≤ 2 ms queue delay) → anomaly score and alert flag → Kafka `alerts` topic → SIEM/SOAR. Attribution (TreeSHAP/DIFFI) runs in an **asynchronous enrichment stage** only for flows above threshold (~250–500/s), so it never blocks the < 10 ms hot path.
* **Training Mode**: Offline rolling retrains. Isolation Forest retrains **daily** on a sliding 7–14 day window of filtered baseline traffic (minutes of compute). The autoencoder retrains weekly. Per-entity EWMA baselines update **incrementally** in Flink state.
* **Feature Store**: **Feast** with an online **Redis** store for per-entity baselines and windowed aggregates, and an offline store (Parquet/Delta on object storage) for training and point-in-time-correct backtesting.
* **Model Registry**: **MLflow Model Registry**, with ONNX artifacts, the training-window manifest, threshold calibration, and feature schema versioned together for ISO 27001 / SOC 2 auditability.
* **Experiment Tracking**: **MLflow** (tracks Optuna trials, Precision@K, FPR, latency benchmarks per run).
* **Model Serving**: **Triton Inference Server** with the ONNX Runtime C++ backend on edge CPU nodes, with optional GPU for the AE ensemble at high-throughput sites. The robust-statistics baseline runs inside Flink as a fallback scorer.
* **CI/CD Pipeline**: **GitHub Actions / GitLab CI**: unit and schema tests, ONNX export parity tests (sklearn vs ONNX score equality within tolerance), latency/throughput load tests at 500K events/s, red-team replay regression suite, then promotion through the MLflow stages.
* **Monitoring & Drift Detection**: **Prometheus + Grafana** for latency, throughput, consumer lag, and alert rate. **PSI** and KS-tests per feature and on the anomaly-score distribution, plus **ADWIN / Page-Hinkley** on streaming alert rates to catch abrupt shifts. **Evidently AI** for scheduled drift reports. An alert-budget monitor pages MLOps if the alert rate deviates > 3× from the expected contamination.
* **Deployment Strategy**: **Shadow mode** first (4–6 weeks scoring in parallel with legacy IDS, no SOC exposure), then **canary** by perimeter site/zone (5% → 25% → 100%), with automatic rollback on alert-rate or latency anomalies. Automated isolation actions are enabled only after analyst-validated precision is proven, starting with reversible actions (for example, rate-limiting, quarantine VLAN with auto-expiry).
* **Retraining Strategy**: Scheduled daily (IF) and weekly (AE) retrains, plus **drift-triggered** retraining when feature PSI > 0.2 or the score distribution shifts significantly. Change-management hooks let NOC flag planned topology changes so retraining can be timed accordingly. Phase 2: the LightGBM re-ranker retrains weekly on accumulated SOC dispositions.

---

## 12. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Baseline contamination** (ongoing undetected attacks learned as "normal") | Medium | High | Filter signature-matched flows and known incidents from training windows; use robust subsampling; keep a long-horizon "golden" baseline model to compare against the rolling model; run periodic threat hunts. |
| **Concept drift** (new services, cloud migrations, topology changes cause false-positive storms) | High | High | Daily rolling retrains; PSI/ADWIN drift detection; NOC change-calendar integration; per-segment models; alert-budget guardrails that auto-throttle and escalate. |
| **Alert volume exceeds SOC capacity** (0.5% FPR at 500K/s ≈ 2,500 false flows/s) | High | High | Incident-level correlation (group by entity and time window), severity tiering, SOAR deduplication, threshold set from analyst capacity, Phase 2 supervised re-ranker trained on dispositions. |
| **Precision@K target unattainable as literally defined** | High | Medium | Redefine K relative to the expected anomaly count, or measure on curated audit sets; agree the metric with stakeholders in Phase 1. |
| **Adversarial evasion** (attackers mimic normal traffic or poison the baseline slowly) | Medium | High | Ensemble IF + AE + signatures (diverse detectors); per-entity long-horizon baselines; monitor gradual baseline shifts; red-team adversarial testing each quarter. |
| **Latency SLA breaches** under traffic bursts / DDoS | Medium | High | Micro-batching with bounded queue delay; Kafka backpressure plus horizontal Triton autoscaling; attribution kept off the hot path; fallback to the in-Flink statistical scorer. |
| **Poor or unhelpful explanations** reduce analyst trust | Medium | Medium | Map features to analyst-readable descriptions; show deviation against the entity's own baseline; collect analyst feedback on explanation quality. |
| **Compliance / privacy** (ISO 27001, SOC 2, non-intrusive inspection) | Low | High | Flow metadata only; payload entropy computed at the sensor without content retention; IP pseudonymization in training stores; access-controlled, versioned model artifacts and audit trails in MLflow. |
| **Unsafe automated isolation** (blocking critical business traffic) | Medium | High | Human-in-the-loop for high-impact actions; allow-list of critical assets; reversible, auto-expiring containment only; staged enablement after the shadow period. |

---

## 13. Implementation Roadmap

| Phase | Activities | Duration |
| :--- | :--- | :--- |
| **1. Business Understanding** | Align SOC, CISO, NOC on KPIs; fix Precision@K and FPR definitions (incident-level vs flow-level); define alert budget and automated-response policy. | 2 weeks |
| **2. Data Collection** | Kafka topics and schemas for NetFlow/IPFIX; data contracts with network teams; retain 30–90 days in the offline store; assemble audit sets, signature-hit history, red-team captures. | 3 weeks |
| **3. Data Preparation** | Schema validation, deduplication, protocol-aware missing-value handling, benign heavy-hitter allow-lists, baseline contamination filtering. | 2 weeks |
| **4. Feature Engineering** | Flink windowed per-entity aggregates; Feast online/offline store integration; cyclical time features; point-in-time-correct training datasets. | 4 weeks |
| **5. Model Selection** | Deploy the robust-statistics baseline; benchmark IF vs EIF vs AE (plus LOF/OCSVM on samples for completeness) on temporal backtests and red-team injections. | 2 weeks |
| **6. Training** | Per-segment Isolation Forest training pipeline; AE training on clean baselines; ONNX export and parity tests. | 2 weeks |
| **7. Hyperparameter Tuning** | Optuna search under latency constraints; threshold calibration to the alert budget. | 2 weeks |
| **8. Evaluation** | Precision@K, FPR, per-attack-family recall, MTTD in red-team exercises; analyst review of top-3 attributions; compliance review. | 2 weeks |
| **9. Deployment** | Triton on edge nodes; CI/CD with latency and throughput load tests; shadow mode alongside legacy IDS (4–6 weeks), then canary rollout by site. | 6–8 weeks |
| **10. Monitoring** | Grafana dashboards (latency, throughput, PSI, score distribution, alert rate); ADWIN/Page-Hinkley alerting; runbooks and fallback drills. | 2 weeks (parallel with 9) |
| **11. Continuous Improvement** | SOC feedback capture → LightGBM semi-supervised re-ranker; IF + AE ensemble; graph-based lateral-movement detection; staged enablement of automated isolation. | Ongoing |

---

## 14. Final Recommendation

Deploy a **streaming Isolation Forest anomaly detector** over enriched per-flow and windowed per-entity NetFlow features. Serve it as ONNX on Triton at the edge for sub-3 ms P99 scoring, and attach TreeSHAP/DIFFI top-3 feature attribution asynchronously to every alert. Benchmark it against a robust statistical baseline, which also serves as the availability fallback. Add a **dense autoencoder** to form a rank-normalized ensemble when stealthy correlated anomalies need coverage, and train a **LightGBM re-ranker on SOC dispositions** to drive the ≥ 65% noise reduction. This combination should cut zero-day MTTD from 48 hours to under 30 seconds, while keeping the system explainable, auditable, and affordable at 500K events/s.

---

## 15. Confidence Level

* **Confidence**: **Medium-High**
* **Reasoning**: Isolation Forest is the most mature and best-matched algorithm for label-free tabular anomaly detection under tight latency and explainability constraints. The serving stack (Kafka/Flink/Feast/Triton/ONNX) is already set by the problem statement and is well proven at this scale. Confidence is held below "High" by (1) the lack of labels, which makes offline accuracy estimates depend on audit sets, red-team data, and public benchmarks that may not represent this network; (2) the arithmetic conflict between the Precision@Top-1% target and the 0.05–0.1% contamination rate, which needs the metric redefined; and (3) the high operational risk of concept drift and alert-volume management at this event rate.
* **Key Assumptions**:
  * At least 30–90 days of historical flow logs are retained and accessible for baseline training and backtesting.
  * Historical audit sets / incident records and red-team exercises can supply enough weak labels for evaluation and threshold calibration.
  * Payload entropy is computed at the sensor as a scalar statistic, consistent with non-intrusive inspection, and no payload content is stored.
  * Alerts are consumed at the incident level (correlated and deduplicated) by a SIEM/SOAR, not as raw per-flow alerts.
  * Edge nodes have enough CPU capacity for micro-batched ONNX inference at their share of the 500K events/s load (GPU optional).
  * Automated isolation starts with reversible, low-blast-radius actions under a human-approved policy.
