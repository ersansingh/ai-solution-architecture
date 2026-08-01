# Deep Learning Problem Statement Template

> **Paradigm**: Deep Learning (Computer Vision / Speech & Audio / Multi-Modal / Complex Sequential Data)  
> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`

---

## 1. Business Objective & Problem Definition
* **Business Objective**: [Extract complex perceptual features and perform automated perception, vision, speech, or multi-modal analysis]
* **Target Domain**: [e.g., Industrial Quality Control / Medical Imaging / Video Surveillance / Speech Recognition / Autonomous Driving]
* **Current Baseline**: [e.g., Manual human inspection / Classical OpenCV filtering / Heuristic signal thresholds]

---

## 2. Modality & Task Specification
* **Target Data Modality**:
  * [ ] Image / Video Data
  * [ ] Audio / Speech Signals
  * [ ] Complex Multi-Modal (Text + Image + Tabular)
  * [ ] Graph / Mesh / Spatial Data
* **Task Type**: [Classification / Object Detection / Instance Segmentation / Speech-to-Text / Feature Embedding]
* **Input Resolution / Format**: [e.g. 1080p video @ 30 FPS / 512x512 RGB images / 16kHz WAV audio]

---

## 3. Dataset & Compute Characteristics
* **Training Data Size**: [Number of labeled samples, total dataset volume in GB/TB]
* **Pre-trained Backbone Availability**: [ImageNet pre-trained / COCO / Wav2Vec2 / Whisper]
* **Data Augmentation Strategy**: [Random Crop, Flip, Color Jitter, Mixup, CutMix, SpecAugment]
* **Training Hardware**: [Available GPU clusters e.g., 8x NVIDIA H100 / A100 / RTX 4090]

---

## 4. Performance & Deployment SLAs
* **Accuracy Metrics**: [mAP@0.5:0.95 / Top-1 Accuracy / Dice Coefficient / Word Error Rate (WER)]
* **Inference Speed SLA**: [FPS requirement e.g. ≥ 30 FPS / Latency < 33 ms]
* **Serving Edge Constraints**: [NVIDIA Jetson / Android Mobile / TensorRT / ONNX INT8 Quantization]

---

## 5. Security & Safety Constraints
* **Explainability**: [Grad-CAM / Integrated Gradients / Attention Heatmaps]
* **Safety Protocols**: [Fail-safe defaults for high-risk automated vision/speech controls]
