# Phase 7 – Model Debugging, Model Registry, and Model Governance

## Lab Guide: Preparing the Model for Production Using Amazon SageMaker Debugger and Model Registry

**Lab Duration:** **2–2.5 Hours**

---

# Phase Objective

By the end of Phase 6, participants have:

* Built multiple models
* Optimized hyperparameters
* Evaluated model performance
* Generated explainability reports
* Verified business KPIs

Before deploying a model into production, enterprise organizations must ensure that:

* The model trained correctly.
* There are no hidden training issues.
* The model is versioned and governed.
* Every model can be audited.
* The correct version is promoted to production.

In this phase, participants will use:

* **Amazon SageMaker Debugger**
* **Amazon SageMaker Model Registry**
* **Model Governance Best Practices**

This phase focuses on **production readiness** rather than prediction accuracy.

---

# Learning Objectives

After completing this phase, participants will be able to:

* Understand common ML training issues.
* Use SageMaker Debugger to inspect training jobs.
* Detect overfitting and unstable training.
* Register models in SageMaker Model Registry.
* Manage model versions.
* Approve or reject model versions.
* Understand enterprise model governance.

---

# Enterprise Architecture

```text
                Training Job
                     │
                     ▼
          SageMaker Debugger
                     │
     ┌───────────────┴───────────────┐
     ▼                               ▼
 Training Analysis             Debug Reports
     │                               │
     └───────────────┬───────────────┘
                     ▼
            Approved Model
                     │
                     ▼
         SageMaker Model Registry
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    Pending Approval      Approved Model
          │                     │
          └──────────┬──────────┘
                     ▼
          Production Deployment
```

---

# Enterprise Model Lifecycle

```text
Raw Data
     │
     ▼
Training
     │
     ▼
Evaluation
     │
     ▼
Debugger
     │
     ▼
Model Registry
     │
     ▼
Approval
     │
     ▼
Deployment
```

---

# Why Model Governance Matters

Imagine a bank deploys a fraud detection model.

Three months later:

* Customers complain.
* Accuracy drops.
* Regulators ask:

> "Which model made this prediction?"

Without version control:

* Impossible to answer.

With Model Registry:

Everything is recorded:

* Model version
* Training dataset
* Hyperparameters
* Metrics
* Approval history
* Deployment history

---

# Input

From Phase 6

```text
Best Model

Evaluation Metrics

SHAP Report

Clarify Report
```

---

# Expected Output

```text
Debugger Report

Training Analysis

Registered Model

Approved Model Version

Model Metadata
```

---

# Task 1 – Understand Training Problems

Common issues during ML training

| Problem             | Impact                        |
| ------------------- | ----------------------------- |
| Overfitting         | Poor generalization           |
| Underfitting        | Low accuracy                  |
| Exploding gradients | Training instability          |
| Vanishing gradients | Slow convergence              |
| Dead neurons        | Ineffective learning          |
| Data leakage        | Unrealistically high accuracy |

Discussion

Which problems are likely in tree-based models?

Which are more common in deep learning?

---

# Task 2 – Enable SageMaker Debugger

Debugger continuously monitors training.

Instead of manually inspecting logs,

Debugger captures

* tensors
* gradients
* weights
* losses

Configure during training.

Example

```python
from sagemaker.debugger import Rule

from sagemaker.debugger import rule_configs

rules = [

Rule.sagemaker(

rule_configs.loss_not_decreasing()

),

Rule.sagemaker(

rule_configs.overtraining()

)

]
```

Attach rules to the estimator.

```python
xgb.rules = rules
```

Discussion

Why automate debugging?

---

# Task 3 – Launch Training with Debugger

Re-run the optimized training job.

Debugger automatically collects:

* Training Loss
* Validation Loss
* Metrics
* Resource utilization

---

Expected Output

Training job generates debugging artifacts.

---

# Task 4 – Inspect Debugger Output

Navigate

```text
Amazon SageMaker

↓

Training Jobs

↓

Debugger
```

Observe

* Rule status
* Violations
* Tensor data
* Captured metrics

---

Discussion

What happens if the validation loss increases while training loss continues to decrease?

Expected Answer

Overfitting.

---

# Task 5 – Analyze Training Curves

Debugger visualizes

Training Loss

Validation Loss

Example

```text
Loss

│\
│ \
│  \
│   \____ Training
│
│        /
│       /
│______/________ Validation
```

Discussion

Which epoch should training stop?

Introduce:

Early Stopping.

---

# Task 6 – Review Resource Utilization

Debugger also records

* CPU
* GPU
* Memory

Discussion

Could a larger instance reduce training time?

Would it increase cost?

---

# Task 7 – Create a Model Package Group

Navigate

```text
Amazon SageMaker

↓

Model Registry

↓

Create Model Package Group
```

Example

```text
Customer-Churn-Models
```

Purpose

Groups all future versions.

---

# Task 8 – Register the Model

Using the SageMaker SDK.

Example

```python
from sagemaker.model import Model

model = Model(
    image_uri=xgb.image_uri,
    model_data=xgb.model_data,
    role=role
)

model.register(

content_types=["text/csv"],

response_types=["text/csv"],

model_package_group_name="Customer-Churn-Models"

)
```

Expected Result

Version 1 appears.

---

# Task 9 – Add Model Metadata

Document

| Property        | Example      |
| --------------- | ------------ |
| Algorithm       | XGBoost      |
| Dataset Version | v1.0         |
| Accuracy        | 92%          |
| ROC AUC         | 0.95         |
| Recall          | 86%          |
| Training Date   | Current Date |
| Owner           | ML Team      |

Discussion

Why document metadata?

---

# Task 10 – Review Model Versions

Navigate

```text
SageMaker

↓

Model Registry
```

Observe

```text
Customer-Churn-Models

Version 1

Version 2

Version 3
```

Discussion

Why keep multiple versions?

---

# Task 11 – Change Approval Status

Possible states

```text
Pending Manual Approval

↓

Approved

↓

Rejected
```

Discussion

Who approves models?

Examples

* Lead Data Scientist
* ML Platform Team
* AI Governance Board

---

# Task 12 – Compare Model Versions

Example

| Version | Accuracy | Recall | Status   |
| ------- | -------- | ------ | -------- |
| V1      | 91%      | 83%    | Approved |
| V2      | 92%      | 86%    | Approved |
| V3      | 90%      | 88%    | Pending  |

Discussion

Would you deploy Version 2 or Version 3?

---

# Task 13 – Model Lineage

Explain

Model Lineage connects

```text
Dataset

↓

Training Job

↓

Experiment

↓

Model

↓

Endpoint
```

Benefits

* Auditability
* Compliance
* Root Cause Analysis

---

# Task 14 – Review Model Governance

Enterprise governance includes

* Versioning
* Metadata
* Approval Workflow
* Audit Trail
* Rollback Capability

Discussion

What happens if Version 3 fails in production?

Expected Answer

Rollback to Version 2.

---

# Best Practices

* Register every model, not just production models.
* Never overwrite model artifacts.
* Record dataset and code versions.
* Use manual approval before deployment.
* Integrate Model Registry with CI/CD pipelines.
* Enable Debugger for production training jobs.

---

# Deliverables

Participants should submit:

1. SageMaker Debugger report.
2. Screenshots of Debugger rules.
3. Model Package Group.
4. Registered model versions.
5. Model metadata.
6. Approval status screenshots.
7. Model governance summary.

---

# Validation Checklist

| Validation                  | Expected Result |
| --------------------------- | --------------- |
| Debugger enabled            | ✓               |
| Training analyzed           | ✓               |
| Overfitting checked         | ✓               |
| Model Package Group created | ✓               |
| Model registered            | ✓               |
| Metadata added              | ✓               |
| Approval status assigned    | ✓               |
| Model lineage available     | ✓               |

---

# Discussion Questions

1. What problems can SageMaker Debugger detect during training?
2. Why is model versioning essential in regulated industries?
3. What information should always accompany a registered model?
4. Why should model approval be a manual governance step?
5. How does model lineage simplify incident investigations?
6. What are the risks of deploying an unregistered model?

---

# Transition to Phase 8

At the end of this phase, participants have a **production-approved, versioned, and governed model** stored in the **SageMaker Model Registry**. The model is now ready to serve predictions.

In **Phase 8 – Model Deployment and Inference**, participants will:

* Deploy the approved model to a **real-time SageMaker Endpoint**.
* Configure endpoint auto scaling and monitoring.
* Invoke the endpoint through the SageMaker Runtime API.
* Build a REST API using **Amazon API Gateway** and **AWS Lambda**.
* Run large-scale predictions using **SageMaker Batch Transform**.
* Compare real-time and batch inference patterns and understand when to use each in enterprise applications.
