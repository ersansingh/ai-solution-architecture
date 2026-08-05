# Phase 9 – Model Monitoring, Data Drift Detection, and Automated Retraining

## Lab Guide: Operating Machine Learning Models in Production Using Amazon SageMaker Model Monitor, CloudWatch, and SageMaker Pipelines

**Lab Duration:** **3–4 Hours**

---

# Phase Objective

Congratulations! By this stage, participants have built a complete production ML solution:

* ✅ Business Problem Definition
* ✅ Data Preparation
* ✅ Feature Engineering
* ✅ Model Training
* ✅ Hyperparameter Tuning
* ✅ Model Evaluation
* ✅ Explainability
* ✅ Model Registry
* ✅ Production Deployment

However, **deploying a model is not the end of the machine learning lifecycle**.

In production, models degrade over time due to:

* Customer behavior changes
* New products
* Market changes
* Economic events
* Data quality issues
* Seasonal variations

This phenomenon is called **Model Drift**.

In this final phase, participants will build an **enterprise-grade MLOps solution** that continuously monitors the model, detects problems, and automatically retrains it when required.

---

# Learning Objectives

By the end of this phase, participants will be able to:

* Monitor production endpoints.
* Detect data quality issues.
* Detect feature drift.
* Detect prediction drift.
* Monitor model performance.
* Build automated retraining pipelines.
* Schedule retraining jobs.
* Understand continuous MLOps.

---

# Enterprise MLOps Architecture

```text
                      Production Endpoint
                               │
                               ▼
                     Incoming Predictions
                               │
                               ▼
                  SageMaker Data Capture
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       CloudWatch Metrics             Captured Data (S3)
               │                               │
               ▼                               ▼
     Endpoint Monitoring         SageMaker Model Monitor
               │                               │
               └───────────────┬───────────────┘
                               ▼
                      Drift Detection
                               │
                      Drift Detected?
                     ┌─────────┴─────────┐
                     │                   │
                    No                  Yes
                     │                   │
                     ▼                   ▼
              Continue Serving   SageMaker Pipeline
                                        │
                                        ▼
                              Retrain New Model
                                        │
                                        ▼
                               Model Registry
                                        │
                              Manual Approval
                                        │
                                        ▼
                             Production Deployment
```

---

# Production Challenges

After six months:

* Customer behavior changes.
* New pricing plans are introduced.
* Usage patterns change.
* More customers use 5G.
* Payment methods evolve.

The model trained six months ago may no longer be accurate.

Without monitoring:

* Revenue loss
* Customer dissatisfaction
* Incorrect predictions

With monitoring:

* Drift detected early
* Automatic retraining
* Continuous improvement

---

# Input

From Phase 8

```text
Production Endpoint

Batch Prediction Pipeline

Approved Model

Feature Store
```

---

# Expected Output

```text
CloudWatch Dashboard

Model Monitor

Data Drift Report

Quality Monitoring

Automated SageMaker Pipeline

Monthly Retraining

Production Monitoring Dashboard
```

---

# Task 1 – Enable Data Capture

## Objective

Capture every inference request.

Navigate

```
SageMaker

↓

Endpoints

↓

Data Capture
```

Enable

* Request Capture
* Response Capture

Store data in

```
s3://teleconnect-churn/monitoring/
```

---

## Why?

Without captured data

↓

No monitoring

↓

No drift detection

---

Expected Result

Every prediction is automatically stored in S3.

---

# Task 2 – Review Captured Data

Navigate

```
Amazon S3

↓

monitoring/

↓

capture/
```

Example

```
Request

Prediction

Timestamp
```

Discussion

Why store production predictions?

---

# Task 3 – Create a Baseline

Model Monitor needs a reference dataset.

Use

```
Training Dataset
```

Generate

* Statistics
* Constraints

Example

```
Mean

Median

Standard Deviation

Minimum

Maximum

Missing Values
```

These become the **baseline profile**.

---

# Task 4 – Configure SageMaker Model Monitor

Navigate

```
SageMaker

↓

Model Monitor

↓

Create Monitoring Schedule
```

Configure

| Setting         | Value                   |
| --------------- | ----------------------- |
| Monitoring Type | Data Quality            |
| Endpoint        | Customer Churn Endpoint |
| Schedule        | Daily                   |
| Baseline        | Training Dataset        |

---

Expected Result

Daily monitoring starts.

---

# Task 5 – Detect Data Drift

Example

Training

```
Average Monthly Charges

₹850
```

Production

```
₹1400
```

Model Monitor detects

```
Feature Drift
```

Discussion

Why is this dangerous?

Because the model has never seen such data.

---

# Task 6 – Detect Missing Features

Example

Training

```
Payment Method

Always Present
```

Production

```
35% Missing
```

Alert generated.

Discussion

What caused it?

Possible answer

Application bug.

---

# Task 7 – Detect Prediction Drift

Example

Training

```
Average Churn Probability

22%
```

Production

```
61%
```

Questions

Has customer behavior changed?

Is the model degrading?

---

# Task 8 – Monitor Endpoint Health

Navigate

```
CloudWatch

↓

Metrics

↓

SageMaker
```

Monitor

* CPU Utilization
* Memory Utilization
* Invocation Count
* Invocation Errors
* 4XX Errors
* 5XX Errors
* Model Latency

Discussion

Which metric impacts customer experience most?

Expected Answer

Latency.

---

# Task 9 – Build a CloudWatch Dashboard

Include

| Widget               | Purpose              |
| -------------------- | -------------------- |
| Endpoint Invocations | Traffic              |
| Average Latency      | Performance          |
| Error Rate           | Reliability          |
| CPU Usage            | Scaling              |
| Memory Usage         | Resource Utilization |
| Drift Alerts         | Model Quality        |

---

Expected Result

Operations dashboard.

---

# Task 10 – Configure CloudWatch Alarms

Create alarms

| Metric      | Threshold |
| ----------- | --------- |
| Latency     | >150 ms   |
| Error Rate  | >2%       |
| CPU         | >80%      |
| Drift Score | >0.2      |

Action

↓

Amazon SNS

↓

Email Notification

Discussion

Who receives alerts?

* ML Engineer
* Platform Team
* Operations Team

---

# Task 11 – Build SageMaker Pipeline

Pipeline stages

```
New Data

↓

Processing

↓

Feature Engineering

↓

Training

↓

Evaluation

↓

Clarify

↓

Model Registry

↓

Manual Approval

↓

Deployment
```

Discussion

Why automate?

---

# Task 12 – Create Processing Step

Pipeline

↓

Processing Job

Input

```
Raw Data
```

Output

```
Processed Dataset
```

---

# Task 13 – Create Training Step

Pipeline

↓

Training Job

Input

```
Processed Data
```

Output

```
Optimized Model
```

---

# Task 14 – Create Evaluation Step

Evaluate

* Accuracy
* Recall
* Precision
* ROC AUC

Decision

```
Metrics Better?

↓

Yes

↓

Register

↓

Else

↓

Reject
```

---

# Task 15 – Register Automatically

Pipeline

↓

Model Registry

↓

Pending Approval

Discussion

Should deployment always be automatic?

Enterprise answer

Usually No.

---

# Task 16 – Schedule Retraining

Navigate

```
Amazon EventBridge
```

Create

Monthly Schedule

```
First Sunday

02:00 AM
```

Target

```
SageMaker Pipeline
```

---

Expected Result

Pipeline runs automatically.

---

# Task 17 – Event-Based Retraining

Instead of time

Trigger when

```
New Dataset

↓

Amazon S3

↓

Event Notification

↓

EventBridge

↓

Pipeline
```

Discussion

Advantages

* Faster adaptation
* Automatic response
* Less manual effort

---

# Task 18 – End-to-End Testing

Simulate

New dataset

↓

Pipeline runs

↓

Model trained

↓

Evaluation passes

↓

Model Registry

↓

Manual approval

↓

Production deployment

---

# Task 19 – Review Complete MLOps Lifecycle

```
Business Problem
        │
        ▼
Data Collection
        │
        ▼
EDA
        │
        ▼
Feature Engineering
        │
        ▼
Training
        │
        ▼
Hyperparameter Tuning
        │
        ▼
Evaluation
        │
        ▼
Explainability
        │
        ▼
Model Registry
        │
        ▼
Deployment
        │
        ▼
Monitoring
        │
        ▼
Retraining
        │
        ▼
Continuous Improvement
```

---

# Best Practices

### Monitoring

* Enable Data Capture for all production endpoints.
* Create a high-quality baseline dataset before enabling monitoring.
* Monitor both infrastructure metrics (CPU, latency, errors) and ML metrics (drift, prediction distribution).

### Retraining

* Retrain only when performance degradation or drift exceeds agreed thresholds.
* Keep retraining pipelines reproducible and version-controlled.
* Validate new models against business KPIs before promotion.

### Governance

* Never deploy directly from a retraining pipeline without governance.
* Route every retrained model through Model Registry and an approval workflow.
* Maintain lineage linking datasets, features, training jobs, model versions, and deployments.

### Operations

* Use CloudWatch dashboards for real-time visibility.
* Configure alarms with Amazon SNS notifications.
* Regularly review monitoring reports to identify emerging issues before they affect customers.

---

# Deliverables

Participants should submit:

1. **CloudWatch dashboard** showing endpoint health.
2. **SageMaker Model Monitor** configuration.
3. **Data Quality Monitoring** report.
4. **Feature Drift** report.
5. **Prediction Drift** analysis.
6. **CloudWatch alarm** configuration.
7. **Amazon SNS** notification setup.
8. **SageMaker Pipeline** definition.
9. **EventBridge** scheduled retraining rule.
10. **End-to-end MLOps architecture diagram** demonstrating the continuous learning workflow.

---

# Validation Checklist

| Validation                               | Expected Result |
| ---------------------------------------- | --------------- |
| Data Capture enabled                     | ✓               |
| Monitoring schedule created              | ✓               |
| Baseline statistics generated            | ✓               |
| Data drift detection configured          | ✓               |
| Endpoint metrics visible in CloudWatch   | ✓               |
| CloudWatch dashboard created             | ✓               |
| CloudWatch alarms configured             | ✓               |
| SageMaker Pipeline created               | ✓               |
| EventBridge schedule configured          | ✓               |
| End-to-end retraining workflow validated | ✓               |

---

# Discussion Questions

1. Why do machine learning models degrade over time?
2. What is the difference between **data drift**, **feature drift**, **prediction drift**, and **concept drift**?
3. Why should retraining be triggered by business rules rather than a fixed schedule alone?
4. Which CloudWatch metrics are most important for customer-facing inference endpoints?
5. Why is human approval still recommended before deploying a retrained model?
6. How do SageMaker Pipelines, Model Registry, and Model Monitor work together to support enterprise MLOps?
7. If a retrained model performs worse than the current production model, what should the pipeline do?

---

# Final Capstone Exercise

As the culmination of the lab, participants should demonstrate the complete enterprise workflow:

1. Upload a new customer dataset to Amazon S3.
2. Trigger the SageMaker Pipeline using EventBridge or an S3 event.
3. Execute data processing, feature engineering, model training, tuning, and evaluation.
4. Register the new model in SageMaker Model Registry.
5. Review evaluation metrics and approve the model.
6. Deploy the approved version to the production endpoint.
7. Validate predictions through the REST API.
8. Observe monitoring metrics and data capture in CloudWatch and Model Monitor.
9. Explain how the solution supports governance, scalability, reliability, and continuous improvement.

---

# Course Completion

Participants who complete all nine phases will have implemented a **production-grade, enterprise MLOps solution** using the AWS SageMaker ecosystem, covering the complete lifecycle from **business problem definition** through **continuous monitoring and automated retraining**. This mirrors the architecture and operational practices used by organizations deploying machine learning at scale.
