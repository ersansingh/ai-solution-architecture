# High-Speed Automated Industrial Surface Defect Detection

## 1. Business Objective & Problem Definition

A semiconductor and precision hardware manufacturer wants to automate real-time surface defect detection on high-speed conveyor production lines. The goal is to detect microscopic surface scratches, cracks, soldering bridges, and pinhole voids on silicon wafers and circuit boards at 60 Frames Per Second (FPS) with zero human intervention.

---

## 2. Business Problem

Manual visual inspection by human quality inspectors is slow, subjective, and prone to fatigue. Over 12% of defective units currently pass inspection unnoticed, leading to expensive product recalls, customer returns, and factory downtime. Existing rule-based OpenCV machine vision systems fail to generalize across lighting variations and subtle non-linear scratch patterns.

---

## 3. Current Process

* Human quality inspectors examining items under magnifying lamps.
* Legacy OpenCV edge-detection scripts (Sobel/Canny filters with hardcoded threshold limits).
* Sample-based manual audit (only 5% of manufactured items audited).

---

## 4. Expected Business Outcome

* Achieve 100% automated inline quality inspection across all manufactured units.
* Reduce defective unit escapes to under 0.1%.
* Increase manufacturing line speed by 35%.
* Save $2.4M annually in scrap reduction and warranty recall costs.

---

## 5. Success Criteria

Business KPIs
* Reduce defect escape rate from 12% to < 0.1%.
* Increase line throughput from 20 units/min to 60 units/min.

Technical KPIs
* mean Average Precision (mAP@0.5:0.95) ≥ 92%.
* Real-Time Latency SLA ≤ 16.6 ms per frame (matching 60 FPS conveyor camera feed).
* Edge hardware VRAM footprint ≤ 8 GB (NVIDIA Jetson AGX Orin deployment).

---

## 6. Data Characteristics & Modality

Data Modality:
* High-resolution RGB & Monochromatic industrial camera feeds (2048x2048 resolution @ 60 FPS).

Dataset Scale:
* 150,000 annotated defect images across 8 defect categories (scratches, cracks, pinholes, bridging, discoloration, misalignment, missing components, cold solder).

Pre-trained Backbone:
* COCO pre-trained weights fine-tuned on industrial surface dataset.

---

## 7. Business & Technical Constraints

* **Inference Speed SLA**: Real-time evaluation in ≤ 16.6 ms per frame on edge hardware.
* **Edge Environment**: Deployment on industrial edge devices (NVIDIA Jetson AGX Orin / Industrial PC with TensorRT).
* **Explainability**: Must generate bounding box coordinates and defect confidence heatmaps (Grad-CAM) for factory audit logs.
