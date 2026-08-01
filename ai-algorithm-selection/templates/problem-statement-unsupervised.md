# Unsupervised Learning Problem Statement Template

> **Paradigm**: Unsupervised Learning (Clustering / Anomaly Detection / Dimensionality Reduction / Representation Learning)  
> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`

---

## 1. Business Objective & Problem Definition
* **Business Objective**: [Discover hidden patterns, segment customers, identify novel anomalies, or reduce feature space without ground truth labels]
* **Target Domain**: [e.g., Customer Segmentation / Network Anomaly Detection / Cybersecurity / Industrial Fault Discovery]
* **Current Baseline**: [e.g., Static threshold rules / Manual heuristic segmentation]

---

## 2. Unsupervised Task & Methodology Specification
* **Unsupervised Paradigm**:
  * [ ] Customer / Data Clustering (Group discovery)
  * [ ] Anomaly & Outlier Detection (Unlabeled novel event detection)
  * [ ] Dimensionality Reduction & Manifold Learning (Feature compression)
  * [ ] Representation Learning (Self-supervised feature extraction)
* **Cluster / Anomaly Definition**: [What constitutes a valid cluster or abnormal event in business terms]
* **Distance / Similarity Metric Preference**: [Euclidean / Cosine / Mahalanobis / Manifold distance]

---

## 3. Data Characteristics
* **Dataset Scale**: [Row count, feature count, embedding dimensions]
* **Data Density & Sparsity**: [Dense numerical, sparse vectors, high-dimensional embeddings]
* **Expected Anomaly Rate (Contamination Factor)**: [e.g. Estimated 0.1% to 2% anomaly rate]
* **Noise & Outlier Levels**: [High background noise, overlapping distribution clusters]

---

## 4. Evaluation & Validity Metrics
* **Internal Cluster Validity Metrics**: [Silhouette Score / Davies-Bouldin Index / Calinski-Harabasz Index]
* **Anomaly Detection Performance**: [Precision@K on historical pseudo-ground-truth audit samples]
* **Reconstruction Metrics**: [Reconstruction Error / MSE for Autoencoders]
* **Latency & Throughput SLA**: [Streaming anomaly evaluation latency e.g., < 10 ms]

---

## 5. Constraints & Downstream Integration
* **Interpretability**: [Must provide cluster centroid profiles or feature attribution for anomaly scores]
* **Deployment Execution**: [Batch clustering refresh vs Real-time streaming anomaly scoring]
