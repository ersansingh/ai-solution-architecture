# AI Algorithm & Model Recommendation Report: High-Speed Industrial Surface Defect Detection

> **Paradigm**: Deep Learning: Supervised Transfer Learning for Real-Time Object Detection, with an Unsupervised Anomaly Guard (Hybrid)
> **Problem Statement**: `lab-ai-algorithm-selection/industrial-defect-detection/industrial-defect-detection.md`
> **Skill**: `.agents/skills/ai-algorithm-selector/SKILL.md`
> **Template**: `.agents/skills/ai-algorithm-selector/templates/algorithm-recommendation-template.md`

---

## 1. Executive Summary

A semiconductor and precision-hardware manufacturer inspects silicon wafers and circuit boards with human inspectors, a 5% manual sample audit, and legacy OpenCV edge-detection scripts. About 12% of defective units get through. The goal is 100% inline inspection of 2048x2048 camera frames at 60 FPS (≤ 16.6 ms per frame) on an NVIDIA Jetson AGX Orin (≤ 8 GB VRAM). The system must detect 8 defect classes, reach mAP@0.5:0.95 ≥ 92%, cut escapes to < 0.1%, and log bounding boxes plus Grad-CAM heatmaps for audit.

We recommend a **single-stage real-time detector, YOLOv8 (s or m) with an added P2 small-object head**. It starts from COCO weights, is fine-tuned on the 150,000 annotated images, and is compiled to **TensorRT INT8** for the Orin. It runs on a **fixture-registered region of interest (ROI) at 1024–1280 px input**, with batched tiling as a fallback when the smallest defects need native resolution. Next to the detector runs an **EfficientAD unsupervised anomaly model**, trained only on defect-free images. It catches defect types the detector was never trained on. Explainability is generated **asynchronously, and only on flagged frames**: boxes are logged inline, and EigenCAM/Grad-CAM heatmaps are rendered off the critical path, so the 16.6 ms budget is not spent on explanations. **RT-DETR (R18/R34)** is the alternative detector. The **incumbent OpenCV rule pipeline** is the baseline that every gain is measured against.

**Confidence is Medium.** This is a well-established paradigm, and the label volume is strong. The binding risk is the combination of **microscopic defects, 2048x2048 frames, 60 FPS, and a single Orin**: the resolution-vs-latency trade-off has to be benchmarked early (Phase 5). The **mAP@0.5:0.95 ≥ 92%** target is also very aggressive for thin, elongated defects such as scratches and cracks. We recommend treating **unit-level recall at a fixed false-reject rate** as the governing KPI, with mAP as the model-selection metric.

---

## 2. Business Problem Analysis

* **Business Objective**: Automate inline visual quality inspection of every manufactured unit, catching microscopic surface defects in real time with no human intervention.
* **Current Process**: Human inspectors work under magnifying lamps. Legacy OpenCV Sobel/Canny scripts use hardcoded thresholds. Only 5% of units are sampled for manual audit.
* **Pain Points**:
  * A 12% defect escape rate drives recalls, returns, and downtime.
  * Inspectors are slow, subjective, and get tired.
  * Rule-based vision breaks under lighting changes and subtle non-linear scratch patterns.
  * Line throughput is capped at 20 units/min by inspection capacity.
* **Expected Outcome**:
  * 100% inline inspection.
  * Escape rate < 0.1%.
  * Line speed up 35% or more (target 60 units/min).
  * About $2.4M/year saved in scrap and warranty costs.
* **Success Criteria**:
  * *Business*: Escape rate from 12% to < 0.1%. Throughput from 20 to 60 units/min.
  * *Technical*: mAP@0.5:0.95 ≥ 92%. ≤ 16.6 ms per frame. ≤ 8 GB VRAM on Jetson AGX Orin.
* **Stakeholders**:
  * *Primary*: Quality engineering, line/process engineering, plant operations.
  * *Secondary*: Quality audit/compliance, customer quality (OEM), MLOps/edge platform team, finance (scrap and warranty savings).
* **Constraints**:
  * Hard real-time edge inference with TensorRT, and no cloud round-trip on the critical path.
  * Explainability through bounding boxes and confidence heatmaps in audit logs.
  * Must hold up under lighting changes and the mix of RGB and monochrome cameras.

---

## 3. AI Suitability Assessment

* **Alternatives Considered**:
  * **Business rules / classical machine vision (OpenCV thresholds, morphology, template matching)**: Already in production. It has failed to generalize across lighting and subtle, non-linear scratch patterns, which is why defects escape. Rules stay useful for *pre-processing*: ROI registration, fiducial alignment, and exposure checks.
  * **Golden-template image differencing**: Works for fully repeatable PCB layouts, but is brittle to sub-pixel misregistration, lighting drift, and texture on wafer surfaces. We keep it as a cheap rule for the *missing component / misalignment* classes during validation, not as the main detector.
  * **SQL / BI dashboards, search, RAG, workflow automation, optimization**: Not applicable. The core task is perceptual (pixels to defect locations).
  * **Generative AI / vision-language models**: Latency is orders of magnitude over a 16.6 ms budget on edge hardware, and there is no accuracy advantage over task-specific detectors when 150K labels exist.
* **Why ML Is Recommended**:
  * The signal is high-dimensional, visual, and non-linear (micro-scratches, pinholes, solder bridges) under changing illumination, which is exactly where learned convolutional features beat handcrafted filters.
  * 150,000 annotated images across 8 classes is enough for supervised fine-tuning.
  * The value is clearly measurable: escapes, throughput, and $2.4M/year.
* **Why ML Is NOT Recommended**: Not applicable to the core detection task. Rules remain the right tool for deterministic pre-processing and for the hard reject/accept actuation logic downstream of the model.

---

## 4. Problem Classification

* **ML Task Category**: Computer Vision: multi-class **object detection** (8 classes: scratch, crack, pinhole, bridging, discoloration, misalignment, missing component, cold solder). A secondary task is **visual anomaly detection** for unseen defect types. Optional: oriented-box or instance-segmentation heads for thin, elongated scratches and cracks.
* **Data Modality**: High-resolution images / video stream (2048x2048 RGB and monochrome at 60 FPS).
* **Learning Paradigm**:
  * *Primary*: **Supervised transfer learning**, with COCO-pretrained detector weights fine-tuned on the industrial dataset.
  * *Secondary*: **Unsupervised (one-class) anomaly detection**, trained on defect-free images.
  * Together these make a **Hybrid** design.
* **Execution Mode**: **Edge real-time streaming.** Inference runs per frame on a Jetson AGX Orin (or an industrial PC with a TensorRT-capable GPU) through a DeepStream/TensorRT pipeline.
* **Classification Reasoning**:
  * The audit requirement asks for *bounding box coordinates* per defect, so plain image classification (defective vs. OK) is not enough. Localization and class are both required, which makes this detection.
  * Classes are known and labeled, so supervised detection is the primary path.
  * A one-class anomaly model is added because the "< 0.1% escapes" goal cannot depend only on the 8 known classes. New process faults create defect types that were never labeled.

---

## 5. Data Assessment

### Data Type
* Images / video stream: 2048x2048 frames at 60 FPS, from both RGB and monochrome industrial cameras.

### Data Quality
* **Dataset Size**: 150,000 annotated defect images, roughly 600 GB–1.2 TB raw (assuming 4–8 MB per 2048² frame, lossless).
* **Features**: Raw pixels. Learned convolutional features replace handcrafted ones. Optional metadata: camera ID, line ID, product SKU/recipe, lighting profile, timestamp.
* **Label Availability**:
  * **Fully labeled** for the 8 known classes (bounding boxes).
  * *Assumption*: Defect-free ("good") frames are abundant but not in the annotated set. They are needed as hard negatives for the detector and as the only training data for the anomaly model.
* **Missing Values**: Not applicable in the tabular sense. The image-level equivalents are missing or incomplete annotations (unlabeled small defects in a labeled image), blur, and over/under-exposure. *Assumption*: moderate. A label audit is required (Section 12).
* **Class Imbalance**:
  * *Expected severe imbalance on two axes*: (1) defect vs. good frames on the live line (defects are rare, given the target escape rate), and (2) between classes (e.g., discoloration and scratches far outnumbering cold solder or cracks).
  * *Assumption*: The rarest class has ≥ 3–5K instances. This must be verified.
* **Outliers**:
  * Unusual lighting, debris and dust (often mistaken for pinholes), reflections on specular wafer surfaces, and new SKUs.
  * These are the main sources of false rejects and should be mined as hard negatives.
* **Historical Depth**: Not stated. *Assumption*: 6–18 months across the current product mix and line conditions.
* **Overall Data Quality**:
  * **Medium-High.** The labeled volume is large, and COCO pretraining is a sound starting point.
  * Two things keep this from "High". First, label consistency for microscopic and ambiguous defects (scratch vs. crack, pinhole vs. dust) is usually the limiting factor in industrial inspection. Second, there is a domain gap between COCO's natural images and specular, monochrome industrial surfaces.

---

## 6. Recommended Learning Paradigm

* **Selected Paradigm**: **Deep Learning: Supervised Transfer Learning (real-time single-stage object detection)**, combined in a **Hybrid** with an **unsupervised one-class visual anomaly detector**.
* **Justification**:
  * Pixel data and subtle, non-linear defect textures need deep convolutional representations. Per the skill's principle, deep learning is justified by the data modality and complexity.
  * Transfer learning from COCO cuts training time and data needs. 150K labels allow full fine-tuning of the backbone, not just the head.
  * A single-stage detector is the only detector family that fits a ≤ 16.6 ms edge budget at this resolution. This matches the reference matrix's "Real-Time Object Detection (Defect Spotting)" scenario: YOLOv8/YOLOv10 primary, RT-DETR secondary.
  * The anomaly guard is a recall safety net for defect types outside the labeled taxonomy. That is necessary to approach a < 0.1% escape rate.
* **Alternatives Considered**:
  * **Two-stage detection (Faster R-CNN / Mask R-CNN)**: Strong on small objects, but typically 40–100+ ms on an Orin at this resolution, so it fails the SLA. It remains useful as an **offline teacher / label-audit model**.
  * **Image classification only (ConvNeXt / EfficientNet-V2 / Swin)**: Gives no localization, so it fails the bounding-box audit requirement. Swin and ViT backbones also run too slowly at 2048².
  * **Pure unsupervised anomaly detection only (PatchCore / EfficientAD)**: Gives no defect class, and coarser localization. It is not enough for class-level quality analytics and root-causing, so it serves as the guard, not the primary model.
  * **Semantic segmentation (U-Net / SegFormer)**: Gives precise defect masks but costs more per frame. We keep it as a Phase 11 option if area-based accept/reject rules are introduced.
  * **Self-supervised pretraining (DINOv2-style) on unlabeled line imagery**: Can close the COCO-to-industrial domain gap. We recommend it as an optional improvement if the fine-tuned mAP plateaus below target.

---

## 7. Top Three Algorithms

### Rank 1 (Recommended): YOLOv8-s/m with P2 Small-Object Head, TensorRT INT8
* **Model Category**: Single-stage anchor-free CNN object detector (CSP backbone + PAN-FPN neck + decoupled head).
* **Specific Implementation**:
  * Ultralytics YOLOv8s (start) or YOLOv8m (if accuracy-bound), with an extra **P2 (stride-4) detection head** for few-pixel defects such as pinholes and micro-cracks.
  * COCO-pretrained, then fully fine-tuned.
  * Exported to ONNX, then built as a TensorRT INT8 engine (entropy calibration on about 1–2K representative frames), with FP16 fallback for sensitive layers.
  * Served through NVIDIA DeepStream on Jetson AGX Orin.
  * YOLOv10 (NMS-free) is a drop-in variant to benchmark, because it removes NMS latency jitter.
* **Input Strategy**:
  * Fixture/fiducial registration crops the frame to the part ROI.
  * The ROI is inferred at 1024–1280 px.
  * If recall on the smallest defects is too low, fall back to **2x2 tiling at 1024 px with batch = 4** (the 2048² frame at native resolution) on a smaller model (n/s), or move to an industrial PC with a discrete RTX-class GPU.
  * The right point is chosen empirically in Phase 5.
* **Why Recommended**:
  * **Business fit and data suitability**:
    * Outputs box coordinates, class, and confidence per defect, which feeds the audit log and the reject actuator directly.
    * Transfers well from COCO to industrial defect datasets.
    * Mosaic and copy-paste augmentation work especially well for rare, small defect classes.
  * **Performance vs. latency compliance**:
    * The s/m models run in single-digit milliseconds at 640 px on an Orin with TensorRT. At 1024–1280 px with INT8, the expected range is about 6–12 ms.
    * That leaves about 4–8 ms for capture, pre-processing (VPI/CUDA), and post-processing, inside the 16.6 ms frame budget.
    * VRAM use is far under 8 GB (< 1.5 GB for the engine plus buffers).
  * **Explainability and production readiness**:
    * Boxes are natively interpretable.
    * EigenCAM/Grad-CAM heatmaps work with YOLO backbones and run asynchronously on flagged frames.
    * The export, quantization, and DeepStream path to Jetson is the most mature edge-detection toolchain available.

### Rank 2 (Alternative): RT-DETR (R18 / R34 backbone), TensorRT FP16
* **Model Category**: Real-time detection transformer (CNN backbone + hybrid encoder + transformer decoder, NMS-free).
* **Why Alternative**:
  * **When to switch**:
    * If YOLO plateaus below the mAP@0.5:0.95 target on cluttered boards with many adjacent defects (e.g., bridged pads, dense pinhole fields). There, set-based NMS-free prediction and global attention reduce duplicate and suppressed boxes.
    * Also if NMS-induced latency jitter breaks the p99 SLA.
  * **Key trade-off vs. Rank 1**:
    * Usually higher accuracy at equal input size, but heavier on Jetson: about 1.5–2x the latency of YOLOv8s at the same resolution.
    * INT8 quantization of the attention layers is less mature, so FP16 is the realistic precision.
    * Slower to converge, with more tuning sensitivity, and the edge tooling ecosystem is less mature.

### Rank 3 (Baseline): Incumbent OpenCV Rule Pipeline (Sobel/Canny + Hardcoded Thresholds)
* **Model Category**: Rule-based classical machine vision.
* **Purpose**:
  * Sets the **performance floor**: it reproduces the current about-12% escape rate on the held-out test set, so every gain is measured against what is deployed today.
  * It also validates the data pipeline, camera triggering, and reject-actuation integration before any model ships.
  * It is replayed in **shadow mode** next to the detector during the pilot.
  * *Secondary ML baseline*: an untuned YOLOv8n at 640 px, which shows what out-of-the-box transfer learning delivers before resolution and head changes.

### Companion Component (Not Ranked): EfficientAD One-Class Anomaly Guard
* A student-teacher plus autoencoder anomaly detector, trained only on defect-free images per product recipe.
* About 2–5 ms on GPU at moderate resolution, run in parallel on the Orin's second compute path (DLA or a CUDA stream).
* Frames with a high anomaly score but no detector box go to **quarantine + human review**, and become the labeling queue for new defect classes.
* PatchCore is the higher-accuracy offline alternative if latency allows.

---

## 8. Algorithm Comparison Table

| Evaluation Dimension | Rank 3 Baseline (OpenCV Rules) | Rank 1 Recommended (YOLOv8-s/m + P2, TRT INT8) | Rank 2 Alternative (RT-DETR-R18/R34, TRT FP16) |
| :--- | :--- | :--- | :--- |
| **Business Fit** | Low (12% escapes) | High | High |
| **Data Suitability** | Low (no use of 150K labels) | High | High |
| **Expected Accuracy** | About 88% defect recall at unit level; mAP not meaningful | mAP@0.5:0.95 about 85–92% (target ≥ 92% likely needs P2 head + tiling + label cleanup); unit-level recall ≥ 99.9% at tuned threshold with anomaly guard | mAP@0.5:0.95 about 87–93%; similar unit-level recall |
| **Interpretability** | Native (explicit thresholds) | High (boxes + async EigenCAM/Grad-CAM) | Medium-High (boxes + attention maps / Grad-CAM; harder to attribute) |
| **Scalability** | Low (per-SKU manual retuning) | High (one engine per line; fleet rollout via OTA) | Medium-High |
| **Training Time** | None (manual tuning) | Moderate (about 1–2 days on 4–8 A100s at 1024–1280 px) | Slow (about 2–4 days; longer convergence) |
| **Inference Latency** | < 5 ms | about 6–12 ms model / ≤ 16.6 ms end-to-end (p99) | about 12–20 ms model; at risk of breaking the SLA on Orin |
| **Computational Cost** | $ | $$ (one Orin per camera station; modest training GPU) | $$$ (may need discrete GPU IPC per station) |
| **Hyperparameter Complexity** | Medium (brittle thresholds) | Medium (input size, anchors-free head, aug, NMS/conf thresholds) | High (query count, LR schedule, denoising settings) |
| **Production Readiness** | High (already deployed) | High (mature ONNX → TensorRT → DeepStream path) | Medium (TensorRT export works; INT8 and Jetson tooling less mature) |

> Accuracy and latency figures are planning estimates based on published Jetson AGX Orin benchmarks and typical industrial-defect fine-tuning results. They must be confirmed in the Phase 5 resolution and latency study.

---

## 9. Feature Engineering Recommendations

1. **Missing Value Handling**:
   * *Image level*: Reject or quarantine frames that fail quality gates (blur via Laplacian variance, exposure histogram, failed fiducial registration) before inference, and log them as "uninspected" rather than "pass".
   * *Label level*: Run an annotation audit for missed small defects. Use the model's high-confidence false positives as candidates for missing labels.
2. **Encoding**:
   * Map the 8 defect classes to integer IDs.
   * Standardize both monochrome and RGB cameras to 3-channel input (replicate the mono channel) so they can share one backbone. Alternatively, train a per-camera-type model if mono accuracy degrades.
   * Encode the product recipe/SKU as metadata, used for anomaly-model selection and stratified evaluation.
3. **Scaling & Normalization**:
   * Per-channel mean/std normalization consistent with the pretrained weights.
   * Letterbox resizing to keep aspect ratio.
   * Flat-field / illumination correction per camera, computed during calibration.
   * All of this is GPU-side (CUDA/VPI) to protect the latency budget.
4. **Feature Selection**: Not applicable to raw pixels. The equivalents are:
   * **ROI cropping** to the registered part area, which removes conveyor background and reduces pixels.
   * **Input-resolution selection**, with tiling only where needed.
5. **Feature Creation**:
   * Fiducial-based registration and alignment, which also gives a geometric check for *misalignment*.
   * Optional golden-reference difference channel for PCB lines with fixed layouts.
   * Multi-scale feature pyramid with a P2 head for microscopic defects.
6. **Outlier Handling**:
   * Hard-negative mining of dust, debris, reflections, and fiducial marks, which are the main false-reject drivers for pinholes and scratches.
   * Glare masking on specular wafer regions.
7. **Class Balancing**:
   * Repeat-factor or class-aware sampling for rare classes (cold solder, crack).
   * Copy-paste augmentation of rare defect instances onto good backgrounds.
   * Classification loss tuned toward rare classes (focal / varifocal loss).
   * Include 20–30% defect-free images in training to calibrate false positives.
   * **Tune the per-class confidence threshold on the PR curve for recall ≥ 99.9%** at an agreed false-reject budget.
8. **Data Augmentation**:
   * Mosaic (disabled for the last about 10 epochs), MixUp, and copy-paste.
   * Photometric augmentations: brightness, contrast, and gamma, which directly address the lighting variation that broke the OpenCV system.
   * Geometric augmentations: horizontal and vertical flips plus 90° rotations, which are valid for wafers and boards. Avoid arbitrary rotations that distort pad geometry.
   * Gaussian and sensor noise, and motion blur that matches conveyor speed.
9. **Domain-Specific Processing**:
   * Hardware-triggered capture synced to the conveyor encoder.
   * Zero-copy capture into GPU memory (DeepStream / NVMM buffers).
   * Pipelined stages (capture, preprocessing, inference, post-processing) so throughput holds at 60 FPS while per-frame latency stays ≤ 16.6 ms.
   * Grad-CAM/EigenCAM heatmaps are rendered asynchronously on a separate low-priority stream, and only for frames with detections or anomaly flags.

---

## 10. Evaluation Metrics

* **Primary Optimization Metric**:
  * **mAP@0.5:0.95** on a held-out, product-stratified test set (target ≥ 92%), used for model selection.
  * **Governing release gate**: **unit-level defect recall ≥ 99.9%** (escape rate < 0.1%) at a **false-reject rate ≤ an agreed budget** (e.g., ≤ 1–2%). This is measured on a production-representative test set with natural defect prevalence.
* **Secondary Metrics**:
  * Per-class AP, recall, and precision, with special attention to pinholes, cracks, and cold solder.
  * mAP@0.5.
  * Small-object AP (AP_S).
  * **End-to-end latency p50 / p99 ≤ 16.6 ms**, sustained 60 FPS throughput, and dropped-frame rate.
  * VRAM ≤ 8 GB, plus power and thermal headroom on the Orin.
  * Anomaly-guard AUROC and PRO score on defect-free vs. novel-defect holdouts.
  * Business KPIs: escape rate, line throughput (units/min), and scrap and warranty cost.
* **Cross-Validation Strategy**:
  * **Group-aware splits** by production lot / wafer batch / board serial, so near-duplicate frames of the same unit never cross train/test.
  * Stratified by defect class and product SKU.
  * A **temporal holdout** (most recent lots) for drift realism.
  * A separate **"unseen SKU / lighting" stress set** for generalization.
* **Hyperparameter Tuning Framework**:
  * **Optuna** (or Ultralytics' built-in tuner backed by **Ray Tune**) over input size, model scale, augmentation strengths, loss weights, and confidence/NMS thresholds.
  * **Each trial is gated by measured TensorRT latency on target hardware**, so this is multi-objective: mAP vs. p99 latency.

---

## 11. Production Architecture & MLOps

* **Inference Mode**: Real-time streaming at the edge. A NVIDIA DeepStream pipeline on Jetson AGX Orin runs camera capture, CUDA preprocessing, TensorRT detector, parallel EfficientAD, and post-processing, then sends the decision to the PLC reject actuator over OPC UA / digital I/O.
* **Training Mode**:
  * Offline, centralized GPU training (on-premises cluster or SageMaker / Azure ML / Vertex AI).
  * Incremental fine-tuning on newly labeled hard cases and new defect classes.
* **Feature Store**: Not applicable for pixel inputs. Use a **versioned image data lake + annotation platform**:
  * S3/MinIO with DVC or LakeFS for dataset versioning.
  * CVAT or Label Studio for labeling.
  * FiftyOne for dataset curation and error analysis.
* **Model Registry**: **MLflow Model Registry**. It stores the PyTorch weights, ONNX, the TensorRT engine *per target hardware/JetPack version*, INT8 calibration cache, thresholds, and the model card.
* **Experiment Tracking**: MLflow or Weights & Biases, logging mAP, per-class AP, and **on-device latency benchmarks** per run.
* **Model Serving**:
  * NVIDIA DeepStream + TensorRT on Jetson. Triton Inference Server is an option on an industrial PC with a discrete GPU.
  * Fleet-managed OTA deployment (e.g., AWS IoT Greengrass, Azure IoT Edge, or K3s on edge nodes).
* **CI/CD Pipeline**: GitHub Actions / GitLab CI with:
  * Data validation.
  * Training.
  * ONNX export.
  * **TensorRT build on a hardware-in-the-loop Jetson runner**.
  * Regression gate on mAP, per-class recall, and p99 latency.
  * Signed artifact promotion.
* **Monitoring & Drift Detection**:
  * Prometheus + Grafana on edge metrics: latency, FPS, dropped frames, GPU and thermals.
  * Evidently AI / Arize on uploaded summaries:
    * Confidence distributions per class.
    * Defect-rate per lot.
    * Image-statistics drift (brightness/contrast histograms, using PSI/KS tests).
    * Anomaly-score drift.
  * Continuous sampling of "passed" units for human audit, to measure the *real* escape rate.
* **Deployment Strategy**:
  * **Shadow mode first.** The model runs alongside human inspection and the OpenCV rules, and logs decisions without acting.
  * Then a **canary** on one line or station, then a staged fleet rollout.
  * Blue-green engine swap on each device, with instant rollback.
* **Retraining Strategy**:
  * **Trigger-based**: image drift past thresholds, a new SKU or recipe, a new defect type surfaced by the anomaly guard, or an escape found in audit.
  * Plus a **scheduled monthly** retrain on accumulated hard examples.
  * Active learning prioritizes low-confidence and anomaly-flagged frames for labeling.

---

## 12. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| Microscopic defects lost at 1024–1280 px downsampling; native-resolution 2048² inference breaks the 16.6 ms SLA on a single Orin | High | High | ROI cropping; P2 head; batched 2x2 tiling with a smaller model; INT8; use DLA for the anomaly guard; budget a discrete-GPU IPC or second Orin per station as contingency; decide by benchmark in Phase 5 |
| mAP@0.5:0.95 ≥ 92% unreachable for thin, elongated scratches/cracks (box IoU penalizes them) | High | Medium | Govern release on unit-level recall at a fixed false-reject rate; evaluate oriented boxes (YOLOv8-OBB) or a seg head for thin classes; renegotiate the per-class mAP target with stakeholders |
| Label noise / inconsistency (scratch vs. crack, pinhole vs. dust, unlabeled small defects) | High | High | Annotation guidelines with visual examples; double-labeling on a sample; inter-annotator agreement; model-assisted label audit (FiftyOne); offline Faster R-CNN teacher for disagreement mining |
| Novel defect types or process faults outside the 8 classes → escapes | Medium | High | EfficientAD one-class guard routes anomalies to quarantine; active-learning loop adds new classes |
| Data / concept drift (lighting aging, camera refocus, new SKUs, process changes) | Medium | High | Flat-field calibration; image-statistics drift monitoring; per-recipe anomaly baselines; drift-triggered retraining; photometric augmentation |
| Excessive false rejects reduce yield and line speed | Medium | Medium | PR-curve threshold tuning per class; hard-negative mining; secondary manual review lane for rejects only; track false-reject rate as a release gate |
| INT8 quantization accuracy loss on small-defect classes | Medium | Medium | Representative calibration set rich in small defects; mixed precision (FP16 for sensitive layers); QAT if PTQ loss > 1 mAP point |
| Latency jitter (NMS, thermal throttling, OS scheduling) breaks p99 | Medium | High | NMS-free YOLOv10 / RT-DETR evaluation; fixed max-detections; MAXN power mode with thermal headroom; real-time kernel; pipelined DeepStream stages |
| Grad-CAM generation inflates latency | Medium | Medium | Off the critical path: render asynchronously on flagged frames only; store raw activations if needed for later rendering |
| Edge security / model tampering on factory network | Low | High | Signed engines; secure boot; network segmentation (OT/IT); role-based OTA deployment |

---

## 13. Implementation Roadmap

| Phase | Activities | Duration |
| :--- | :--- | :--- |
| **1. Business Understanding** | Agree on the governing KPI (unit-level recall at a false-reject budget); confirm per-class criticality and accept/reject rules; define audit-log schema; set the latency/hardware envelope per station | 2 weeks |
| **2. Data Collection** | Inventory the 150K annotated images; collect defect-free frames per SKU/recipe; hardware-triggered capture at production speed; data contracts per camera/line | 3 weeks |
| **3. Data Preparation** | Label audit and guideline refresh; dedup near-identical frames; group-aware train/val/test splits by lot; build stress sets (lighting, new SKU) | 4 weeks |
| **4. Feature Engineering** | ROI registration; flat-field correction; mono/RGB standardization; GPU preprocessing in DeepStream; augmentation pipeline (photometric, copy-paste) | 2 weeks |
| **5. Model Selection** | OpenCV baseline replay; YOLOv8n/s/m vs. YOLOv10 vs. RT-DETR at 640/1024/1280/tiled-2048; **on-device TensorRT latency vs. mAP Pareto study on Jetson AGX Orin**; select resolution and hardware | 3 weeks |
| **6. Training** | Full fine-tuning from COCO with P2 head; EfficientAD per recipe; multi-GPU distributed training | 3 weeks |
| **7. Hyperparameter Tuning** | Optuna multi-objective (mAP, recall vs. p99 latency); per-class threshold optimization on PR curves; INT8 calibration / QAT | 2 weeks |
| **8. Evaluation** | Per-class AP/recall, escape-rate simulation, false-reject rate; robustness on stress sets; Grad-CAM/EigenCAM sanity checks with quality engineers; model card | 2 weeks |
| **9. Deployment** | DeepStream + TensorRT engine build in CI with hardware-in-the-loop; PLC/MES integration; shadow mode alongside humans and OpenCV; canary on one line | 4 weeks |
| **10. Monitoring** | Edge telemetry dashboards (latency, FPS, thermals); confidence/anomaly drift; audit sampling of passed units for true escape rate | 2 weeks (then ongoing) |
| **11. Continuous Improvement** | Active learning from anomaly-flagged and low-confidence frames; drift-triggered and monthly retraining; new-SKU onboarding playbook; evaluate segmentation/OBB heads | Ongoing |

---

## 14. Final Recommendation

Deploy a **COCO-pretrained YOLOv8 (s or m) detector with a P2 small-object head**, fine-tuned on the 150K labeled images and compiled to **TensorRT INT8 on Jetson AGX Orin via DeepStream**. Run it on a registered ROI at 1024–1280 px, with batched tiling or a discrete-GPU fallback, chosen by an early on-device latency-vs-accuracy study. Pair it with an **EfficientAD anomaly guard** for unseen defects, and generate **audit heatmaps asynchronously** so explanations never spend the 16.6 ms budget. Keep **RT-DETR** as the accuracy-driven alternative and the **incumbent OpenCV pipeline** as the shadow baseline. Release on **unit-level recall ≥ 99.9% at an agreed false-reject rate**, which ties model quality directly to the < 0.1% escape and $2.4M/year savings goals.

---

## 15. Confidence Level

* **Confidence**: **Medium**
* **Reasoning**:
  * *High-confidence factors*:
    * Real-time single-stage detection with transfer learning is the industry-standard, production-proven approach for inline visual inspection.
    * 150K labeled images is a strong dataset.
    * The Jetson/TensorRT/DeepStream toolchain is mature.
  * *Factors that lower confidence*:
    * (1) Whether microscopic defects can be detected reliably at an input resolution that fits ≤ 16.6 ms on a single Orin is unproven until benchmarked.
    * (2) mAP@0.5:0.95 ≥ 92% is an aggressive target for thin, elongated defect geometry.
    * (3) Label consistency for microscopic, ambiguous classes is unknown.
    * (4) The proportion and availability of defect-free images is not specified.
* **Key Assumptions**:
  * Defect-free production frames are available in volume per SKU/recipe.
  * The rarest defect class has enough instances (≥ 3–5K) for supervised learning.
  * Parts are fixtured well enough for fiducial-based ROI registration.
  * Hardware-triggered capture synced to the conveyor is feasible.
  * Each camera station gets at least one Jetson AGX Orin, with budget for an IPC/discrete-GPU fallback.
  * Stakeholders accept unit-level recall at a fixed false-reject rate as the governing release KPI alongside mAP.
  * The 60 FPS requirement means per-frame processing of every camera frame, not one frame per unit (the line runs 60 units/min).
