# Enterprise Network Intrusion & Zero-Day Anomaly Detection

## 1. Business Objective & Problem Definition

A global telecommunications and enterprise cybersecurity provider wants to detect zero-day cyber threats, unauthorized network intrusions, and abnormal data exfiltration across its enterprise backbone. The objective is to identify novel security anomalies in real-time without relying on static signature rules or historical threat labels.

---

## 2. Business Problem

Traditional Intrusion Detection Systems (IDS) rely heavily on known threat signatures (e.g., CVE hashes, known malicious IP lists). Attackers frequently bypass signature systems using novel malware variants, encrypted traffic channels, and polymorphic exploits. The security operations center (SOC) receives 500,000 network telemetry events per second, leading to high analyst fatigue and missed zero-day attacks.

---

## 3. Current Process

Current network threat identification relies on:
* Static Snort / Suricata signature rules
* Fixed bandwidth threshold alerts
* Manual firewall log reviews
* Post-incident forensics after data exfiltration has occurred

These legacy approaches fail to detect zero-day attacks and produce over 90% false-positive alert noise.

---

## 4. Expected Business Outcome

* Identify zero-day network threats within 10 seconds of onset.
* Reduce false positive security alerts by at least 65%.
* Prevent high-severity data exfiltration breaches.
* Automate initial threat isolation for the Security Operations Center (SOC).

---

## 5. Success Criteria

Business KPIs
* Reduce Mean Time to Detect (MTTD) zero-day threats from 48 hours to < 30 seconds.
* Reduce SOC alert noise by 65%.
* Maintain 99.99% network monitoring service availability.

Technical KPIs
* Precision@K (Top 1% anomaly score) ≥ 88% on historical audit sets.
* False Positive Rate (FPR) ≤ 0.5%.
* Real-time streaming scoring latency < 10 ms per network packet flow event.
* Ingestion throughput ≥ 500,000 packet flow records per second.

---

## 6. Target Variable / Anomaly Definition

Anomaly Definition:
A network flow or cluster of flow events is classified as anomalous if its multi-dimensional telemetry distribution significantly deviates from the established baseline behavior of normal network traffic.

Target Output:
* **Anomaly Score**: Continuous normalized float $[0.0, 1.0]$.
* **Alert Flag**: Binary (`1` = Anomalous / Threat, `0` = Normal).
* **Attribution**: Top 3 network features contributing to the anomaly score.

---

## 7. Data Characteristics

Dataset Scale:
* 500,000 network flow events per second (~43 billion records per day / 2.5 TB daily log stream).

Features (42 NetFlow/IPFIX attributes):
* Flow duration, packet rates, byte ratios, TCP window sizes, SYN/ACK ratios, payload entropy, port frequencies, inter-arrival time distributions.

Ground Truth Availability:
* Unlabeled live data (Zero historical labels for novel attacks).

Contamination Factor:
* Estimated 0.05% to 0.1% malicious anomaly rate in normal network baseline traffic.

---

## 8. Business & Technical Constraints

* **Latency SLA**: Real-time packet flow scoring in < 10 ms.
* **Compute Constraints**: Must run streaming inference on CPU/GPU edge nodes deployed at perimeter routers.
* **Explainability**: SOC analysts require feature contribution breakdowns (e.g., "Abnormal SYN packet frequency + High outbound entropy") for every triggered alert.
* **Compliance**: ISO 27001, SOC 2 Type II, non-intrusive traffic inspection.

---

## 9. Deployment Environment

* **Streaming**: Apache Kafka / Apache Flink
* **Feature Store**: Feast (Online Redis Store)
* **Serving Microservice**: Triton Inference Server (C++ backend with ONNX Runtime)
* **Monitoring**: Prometheus + Grafana dashboard tracking Population Stability Index (PSI) and anomaly score distributions.
