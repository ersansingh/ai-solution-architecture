# Enterprise AI Algorithm & Model Selection Reference Matrix

> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`  
> **Templates Location**: `.agents/skills/ai-algorithm-selector/templates/`

This reference guide provides comprehensive mappings between problem domains, AI paradigms, data characteristics, operational constraints, and recommended AI models and algorithms.

---

## 1. Supervised Learning Paradigm (Classification, Regression, Time-Series)

| Scenario / Constraints | Primary Recommendation | Secondary / Alternative | Simple Baseline | Key Selection Drivers |
| :--- | :--- | :--- | :--- | :--- |
| **Large Structured Dataset (>1M rows), Mixed Types, High Latency SLA (<50ms)** | **XGBoost / LightGBM** | CatBoost | Logistic Regression / Ridge | Speed, histogram binning, native missing value handling, TreeSHAP support. |
| **High Cardinality Categorical Features (e.g. Zip codes, Store IDs, User Categories)** | **CatBoost** | LightGBM (with categorical features) | Target Encoded Logistic Regression | Native symmetric tree structure and target statistics prevent target leakage. |
| **Small-to-Medium Tabular Data (<100K rows), High Noise** | **Random Forest** | Extra Trees / XGBoost | Decision Tree | Low parameter tuning overhead, resistant to variance and overfitting. |
| **Imbalanced Class Distribution (e.g., Churn 10%, Fraud 0.1%)** | **XGBoost / LightGBM** (with `scale_pos_weight` or Focal Loss) | Balanced Random Forest / XGBoost + SMOTE-NC | Cost-Sensitive Logistic Regression | Gradient boosting with custom weighted loss avoids threshold calibration issues. |
| **Univariate / Low-Dimension Time-Series with Strong Seasonality** | **Prophet / ARIMA / SARIMAX** | ETS (Exponential Smoothing) | Naive / Moving Average | Interpretable trend decomposition, holiday handling, fast convergence. |
| **Multivariate Time-Series with High-Frequency Feature Covariates** | **LightGBM / XGBoost** (Lag & Rolling Window Features) | Temporal Fusion Transformer (TFT) | Vector Autoregression (VAR) | GBDTs with engineered time lags often beat deep networks on structured time-series while training 100x faster. |

---

## 2. Unsupervised Learning Paradigm (Clustering, Anomaly Detection, Representation)

| Scenario / Constraints | Primary Recommendation | Secondary / Alternative | Simple Baseline | Key Selection Drivers |
| :--- | :--- | :--- | :--- | :--- |
| **Unsupervised Tabular Anomaly Detection (Zero Historical Labels)** | **Isolation Forest / Extended Isolation Forest** | Local Outlier Factor (LOF) / One-Class SVM | Z-Score / IQR Thresholding | Subsampling and tree isolation efficiently partition sparse anomalies in multi-dimensional space. |
| **Customer Segmentation on Low/Medium Dimensional Tabular Data** | **K-Means++ / Gaussian Mixture Models (GMM)** | HDBSCAN / Hierarchical Clustering | Heuristic Binning | Centroid and density-based clustering with clear BIC/AIC or Silhouette score validation. |
| **Density-Based Clustering with Arbitrary Cluster Shapes & Noise** | **HDBSCAN** | DBSCAN / Spectral Clustering | K-Means | No requirement to pre-define $k$; robust to non-spherical clusters and background noise. |
| **High-Dimensional Dimensionality Reduction & Visualization** | **UMAP (Uniform Manifold Approximation)** | t-SNE / Truncated SVD | PCA (Principal Component Analysis) | Preserves global and local non-linear structure significantly better than t-SNE with 10x faster execution. |

---

## 3. Reinforcement Learning Paradigm (Decision Making, Bandits, Policy Control)

| Scenario / Constraints | Primary Recommendation | Secondary / Alternative | Simple Baseline | Key Selection Drivers |
| :--- | :--- | :--- | :--- | :--- |
| **Contextual Bandits for Real-Time Personalization & Recommendation** | **LinUCB / Thompson Sampling (LinTS)** | Multi-Armed Bandit (Epsilon-Greedy) | Random A/B Allocation | Balances exploration and exploitation in online environments with low computational overhead. |
| **Continuous Control & Robotics with High-Fidelity Simulator** | **PPO (Proximal Policy Optimization)** | SAC (Soft Actor-Critic) / TD3 | PID Controller | PPO offers clipped surrogate objective stability; SAC provides high sample efficiency for continuous action spaces. |
| **Discrete Action Space Game AI & Autonomous Routing** | **DQN (Deep Q-Network) / Rainbow DQN** | PPO / A2C | Heuristic Greedy Search | Value-based Q-learning with target networks and prioritized experience replay. |
| **Offline Reinforcement Learning from Static Logged Datasets (No Live Simulator)** | **CQL (Conservative Q-Learning) / Implicit Q-Learning (IQL)** | Decision Transformer | Behavioural Cloning | Penalizes out-of-distribution actions to prevent overestimation in static log environments. |

---

## 4. Deep Learning Paradigm (Vision, Speech, Audio, Spatial)

| Scenario / Constraints | Primary Recommendation | Secondary / Alternative | Simple Baseline | Key Selection Drivers |
| :--- | :--- | :--- | :--- | :--- |
| **Image Classification (Product Catalog, Quality Inspection)** | **Swin Transformer / ConvNeXt** | EfficientNet-V2 / ResNet-50 | SVM on HOG Features | Swin Transformer handles hierarchical representations; ConvNeXt offers conv-net speed with transformer accuracy. |
| **Real-Time Object Detection (Video Surveillance, Defect Spotting)** | **YOLOv8 / YOLOv10** | RT-DETR (Real-Time Detection Transformer) | OpenCV Cascade Classifiers | Single-stage detector with sub-20ms inference capability on edge hardware. |
| **Speech-to-Text & Audio Transcription** | **Whisper (OpenAI) / Wav2Vec2** | DeepSpeech | HMM-GMM Acoustic Model | Encoder-decoder transformer trained on 680k hours of multilingual audio. |
| **Graph-Structured Relational Data (Social Networks, Molecular Graphs)** | **GraphSAGE / Relational GCN (RGCN)** | GAT (Graph Attention Network) | Node2Vec + GBDT | Neighborhood aggregation passes messages along graph edges for node classification and link prediction. |

---

## 5. Generative AI & Large Language Models Paradigm (RAG, SLMs, LLMs, Agents)

| Scenario / Constraints | Primary Recommendation | Secondary / Alternative | Simple Baseline | Key Selection Drivers |
| :--- | :--- | :--- | :--- | :--- |
| **Enterprise Knowledge Q&A / Document Search (RAG Pattern)** | **Advanced RAG Pipeline**: Hybrid Search (BM25 + BGE Embeddings) + Cross-Encoder Reranker + Llama-3-8B / Claude 3.5 / GPT-4o | Small Specially-Tuned SLM (e.g. Phi-3.5-mini) | Standard Dense Vector RAG | Reranking eliminates retrieval noise; hybrid search handles exact keyword codes and domain terms. |
| **Low-Latency On-Premise / Edge Text Generation (<100ms first token)** | **Quantized SLM (Llama-3-8B-Instruct INT4/INT8 via vLLM / Ollama)** | Mistral-7B-Instruct | Rule-based template generator | Sub-10B models fit into modest GPU/VRAM hardware, maintain high instruction-following accuracy. |
| **Complex Multi-Step Reasoning & Autonomous Tool Execution (Agent Pattern)** | **ReAct / Function Calling Agent**: Claude 3.5 Sonnet / GPT-4o / DeepSeek-V3 / Llama-3.3-70B | Fine-tuned Llama-3-70B with Instructor / Toolformer | Single-prompt LLM chain | Superior function calling syntax reliability, low hallucination rates in agentic loops. |
| **Domain-Specific Text Structuring & Extraction (Legal/Financial)** | **Fine-Tuned Llama-3 / Qwen-2.5** (via LoRA / QLoRA with Instructor / Outlines JSON schema enforcement) | Claude 3.5 Sonnet (with JSON Mode) | Regex / Rule Parsers | Structured output generation guarantees schema adherence; LoRA reduces fine-tuning GPU cost by 90%. |

---

## 6. Operational Constraint Selection Spectrum

### Latency vs Accuracy Spectrum

```
[Strict Latency < 10ms]  ---> Linear Models, Naive Bayes, LinUCB, Isolation Forest
[Low Latency 10 - 50ms]  ---> LightGBM, XGBoost, ONNX Quantized YOLO / Small Models
[Medium Latency 50-300ms] ---> RoBERTa, DeBERTa, Small Language Models (SLMs < 8B)
[High Latency > 500ms]   ---> Large LLMs (70B+), RAG Pipelines, Multi-Agent Loops, Deep RL
```

### Explainability vs Performance Spectrum

```
[Full Transparency]   ---> Linear Regression, Decision Trees, K-Means, Rule Systems
[High Interpretability]---> XGBoost / LightGBM + SHAP / LIME Tree Explainer
[Medium Interpretability] -> DeBERTa / BERT + Attention Weights / Integrated Gradients
[Black-Box / Complex] ---> Deep Vision Transformers, Multi-Agent Systems, Deep RL (Requires Guardrails & Auditing)
```
