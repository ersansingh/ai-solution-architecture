# AI Algorithm & Model Recommendation Report: Enterprise Network Intrusion Anomaly Detection

> **Paradigm**: Unsupervised Learning (Anomaly Detection / Dimensionality Reduction)  
> **Problem Statement**: `ai-algorithm-selection/use-cases/network-anomaly-detection/network-anomaly-detection.md`

---

## 1. Executive Summary & Problem Classification

### Overview
This recommendation report evaluates unsupervised AI algorithms for real-time zero-day network anomaly detection across 500,000 telemetry events per second. Due to the complete absence of ground-truth labels for novel threats and strict <10 ms latency SLAs, traditional supervised classification cannot be applied.

We recommend a **Hybrid Unsupervised Pipeline** combining **Extended Isolation Forest (EIF)** for fast high-throughput streaming tabular anomaly scoring, alongside a **Variational Autoencoder (VAE)** for complex non-linear feature interaction modeling, paired with **UMAP** for 2D topology clustering in SOC monitoring dashboards.

### Problem Domain Classification
* **ML Task Category**: Unsupervised Anomaly & Outlier Detection
* **Data Modality**: Streaming Telemetry (NetFlow/IPFIX 42 continuous & discrete features)
* **Learning Paradigm**: Unsupervised / Self-Supervised Baseline Density Estimation
* **Execution Mode**: Real-Time Streaming Ingestion via Apache Flink + C++ Triton ONNX Inference Microservice

---

## 2. Recommended AI Algorithms & Models

### Primary Recommendation: Extended Isolation Forest (EIF) + C++ ONNX Engine

* **Model Category**: Tree-Based Unsupervised Anomaly Isolation
* **Specific Architecture**: Extended Isolation Forest (EIF) compiled to ONNX Runtime
* **Rationale for Recommendation**:
  * **Arbitrary Cut Hyperplanes**: EIF cuts hyperplanes at random angles, solving the axis-parallel constraint bias of standard Isolation Forest on correlated network features (e.g. byte rate vs packet count).
  * **Streaming Latency SLA**: Sub-3ms inference latency per event, enabling 500,000 QPS throughput across scaled C++ execution nodes.
  * **No Distribution Assumptions**: Non-parametric algorithm that does not assume Gaussian traffic distributions.

### Secondary Candidate: Variational Autoencoder (VAE)

* **Model Category**: Deep Generative Reconstruction Architecture
* **Rationale & Trade-offs**:
  * **Reconstruction Error Thresholding**: VAE learns latent normal network representations. Anomalous traffic yields high reconstruction loss ($MSE > \tau$).
  * **Trade-off**: Higher GPU compute requirement during inference (~8 ms latency vs ~2 ms for EIF). Recommended as a parallel scoring model for high-risk corporate subnets.

### Baseline Model Strategy

* **Simple Baseline**: Robust Z-Score / Median Absolute Deviation (MAD) on univariate rolling traffic features.
* **Purpose**: Establishes minimum anomaly floor and monitors basic volumetric DDoS spikes.

---

## 3. Comparative Evaluation & Trade-off Matrix

| Evaluation Criteria | Baseline (Robust Z-Score) | Primary (Extended Isolation Forest) | Secondary (Variational Autoencoder) | Alternative (One-Class SVM) |
| :--- | :--- | :--- | :--- | :--- |
| **Detection of Zero-Day Anomalies** | Low (Volumetric only) | **High (Multi-feature isolation)** | **Very High (Latent reconstruction)** | Moderate |
| **Inference Latency (p95)** | < 1 ms | **< 3 ms (Compiled ONNX)** | ~ 8 ms (GPU) | ~ 45 ms (Memory bound) |
| **Throughput Capacity** | > 1,000,000 QPS | **> 500,000 QPS / Node** | ~ 100,000 QPS / Node | ~ 15,000 QPS / Node |
| **Memory / Compute Footprint** | Negligible | **Low (RAM < 2 GB)** | Moderate (GPU VRAM) | High (O($N^2$) support vectors) |
| **Explainability** | Single Feature | **Feature Attribution via Path Length** | Reconstruction Error per Feature | Complex Dual Weights |
| **Handling Correlated Features** | Poor | **Excellent (Hyperplane slicing)** | Excellent | Moderate |
| **Estimated Infrastructure Cost** | $100/mo | **$1,200/mo** | $3,800/mo | $5,500/mo |

---

## 4. Preprocessing & Feature Engineering Strategy

1. **Robust Scaling**: Apply `RobustScaler` (median & IQR) to handle extreme volumetric outliers in baseline traffic without biasing scaling parameters.
2. **Payload Entropy & Ratio Features**:
   * Compute payload Shannon Entropy: $H(X) = -\sum P(x) \log_2 P(x)$ to detect encrypted exfiltration channels.
   * Compute SYN-to-ACK ratios and byte-per-packet velocity.
3. **Contamination Calibration**: Calibrate decision threshold $\tau$ at contamination factor $\alpha = 0.001$ (0.1% expected top-anomaly rate).

---

## 5. Model Optimization & Deployment Serving

* **Compilation**: Export EIF model to ONNX format using `skl2onnx`.
* **Serving Microservice**: Deploy ONNX Runtime within Triton Inference Server with multi-thread execution ONNX EP (Execution Provider).
* **Alert Dashboard**: Use **UMAP** to project high-dimensional NetFlow embeddings into a 2D interactive Grafana map for SOC analysts to visually isolate threat clusters.
