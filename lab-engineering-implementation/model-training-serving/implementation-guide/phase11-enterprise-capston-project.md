# Phase 11 – Enterprise Capstone Project

## Implementation Guide: Designing, Building, and Operating a Production-Ready Customer Churn Prediction Platform

**Lab Duration:** **6–8 Hours (or 1–2 Days)**

---

# Phase Objective

This capstone project consolidates everything learned throughout the course into a single end-to-end implementation.

Participants will act as an **AI Solutions Architect**, **ML Engineer**, and **MLOps Engineer** responsible for delivering a complete production-ready machine learning solution for a telecommunications company.

Unlike previous phases, this project provides only business requirements. Participants must design, build, deploy, and operate the solution independently using AWS SageMaker and supporting AWS services.

---

# Business Scenario

TeleConnect, a global telecommunications provider with more than **30 million customers**, wants to reduce customer churn by identifying customers likely to leave within the next 90 days.

Current Challenges:

* Annual churn rate of **18%**
* Manual customer retention process
* No centralized ML platform
* Limited model governance
* No production monitoring
* No automated retraining

Executive leadership has approved an AI initiative and expects a production-ready solution.

---

# Business Requirements

The solution must:

* Predict customer churn probability
* Support both batch and real-time inference
* Provide explainable predictions
* Detect model drift automatically
* Retrain models automatically
* Support model governance
* Meet enterprise security requirements
* Be scalable and highly available

---

# Success Criteria

| KPI                   | Target                             |
| --------------------- | ---------------------------------- |
| ROC AUC               | ≥ 0.90                             |
| Precision             | ≥ 85%                              |
| Recall                | ≥ 80%                              |
| Endpoint Latency      | <150 ms                            |
| Endpoint Availability | 99.9%                              |
| Batch Prediction      | 5 million customers in <30 minutes |
| Automated Retraining  | Monthly or drift-based             |
| Explainability        | SHAP report generated              |
| Governance            | Model Registry approval workflow   |

---

# Expected Architecture

```text
                Customer Data Sources
                        │
                        ▼
                 Amazon S3 Data Lake
                        │
                        ▼
          SageMaker Processing / Feature Engineering
                        │
                        ▼
             SageMaker Feature Store
                        │
                        ▼
          SageMaker Training & Tuning Jobs
                        │
                        ▼
         Evaluation + Clarify + Debugger
                        │
                        ▼
          SageMaker Model Registry
                        │
               Manual Approval
                        │
        ┌───────────────┴────────────────┐
        ▼                                ▼
 Real-Time Endpoint              Batch Transform
        │                                │
        ▼                                ▼
 API Gateway + Lambda             Marketing Systems
        │
        ▼
 Business Applications
        │
        ▼
 CloudWatch + Model Monitor
        │
        ▼
 SageMaker Pipeline + EventBridge
        │
        ▼
 Automated Retraining
```

---

# Project Deliverables

Participants are expected to deliver the following components.

## 1. Solution Architecture

Create an architecture diagram showing:

* Data ingestion
* Storage
* Feature engineering
* Training
* Evaluation
* Model Registry
* Deployment
* Monitoring
* Retraining

---

## 2. Data Lake

Implement the following Amazon S3 structure:

```text
teleconnect-churn/

raw-data/
processed-data/
feature-store/
training/
models/
predictions/
monitoring/
artifacts/
pipelines/
logs/
```

---

## 3. Data Processing

Implement:

* Missing value handling
* Duplicate removal
* Outlier handling
* Encoding
* Scaling
* Feature engineering

Generate at least:

* Customer Lifetime Value
* Customer Risk Score
* Payment Risk
* Complaint Ratio
* Engagement Score

---

## 4. Feature Store

Create a SageMaker Feature Group containing:

* Customer features
* Engineered features
* Event timestamp

Demonstrate feature reuse.

---

## 5. Model Development

Train and compare:

* XGBoost
* Linear Learner
* Random Forest

(Optional)

* LightGBM

Track experiments using SageMaker Experiments.

---

## 6. Hyperparameter Optimization

Optimize:

* Learning rate
* Tree depth
* Number of trees
* Child weight
* Gamma
* Subsample

Select the best model.

---

## 7. Model Evaluation

Produce:

* Accuracy
* Precision
* Recall
* F1 Score
* ROC AUC
* Confusion Matrix
* ROC Curve
* Precision–Recall Curve

---

## 8. Explainability

Generate:

* SHAP feature importance
* Local prediction explanations
* Global explainability report
* Bias analysis using SageMaker Clarify

---

## 9. Model Governance

Register the selected model.

Include:

* Version
* Metrics
* Dataset version
* Training date
* Approval status

---

## 10. Real-Time Inference

Deploy a SageMaker endpoint.

Requirements:

* Auto Scaling
* Health checks
* API invocation
* REST API using API Gateway and Lambda

---

## 11. Batch Prediction

Run Batch Transform for a large customer dataset.

Store predictions in Amazon S3.

---

## 12. Monitoring

Configure:

* CloudWatch dashboard
* CloudWatch alarms
* Model Monitor
* Data Capture

Monitor:

* Latency
* Errors
* Drift
* Feature quality

---

## 13. Automated Retraining

Implement a SageMaker Pipeline that performs:

```text
Data Processing

↓

Feature Engineering

↓

Training

↓

Evaluation

↓

Model Registry

↓

Manual Approval

↓

Deployment
```

Trigger:

* Monthly via EventBridge
* On new training data arrival

---

## 14. CI/CD

Automate:

* Code validation
* Unit testing
* Pipeline execution
* Model registration
* Staging deployment
* Production deployment
* Rollback

---

# Project Acceptance Tests

Participants must successfully demonstrate:

| Test                     | Expected Result                             |
| ------------------------ | ------------------------------------------- |
| Upload new training data | Pipeline starts automatically               |
| Train new model          | Training completes successfully             |
| Evaluate model           | KPIs achieved                               |
| Register model           | New version appears in Model Registry       |
| Approve model            | Deployment proceeds                         |
| Invoke REST API          | Prediction returned                         |
| Run Batch Transform      | Output stored in S3                         |
| Simulate feature drift   | Alert generated                             |
| Trigger retraining       | Pipeline executes successfully              |
| Validate rollback        | Previous model restored if deployment fails |

---

# Presentation Requirements

Each team should prepare a **20–30 minute technical presentation** covering:

1. Business problem and objectives
2. Solution architecture
3. Data preparation approach
4. Feature engineering strategy
5. Model comparison and selection
6. Hyperparameter tuning results
7. Explainability and bias findings
8. Deployment architecture
9. Monitoring and retraining strategy
10. Lessons learned and future improvements

---

# Evaluation Rubric

| Category                     | Weight |
| ---------------------------- | -----: |
| Architecture Design          |    15% |
| Data Engineering             |    10% |
| Feature Engineering          |    10% |
| Model Performance            |    20% |
| Explainability & Bias        |    10% |
| Deployment & APIs            |    10% |
| Monitoring & Retraining      |    10% |
| CI/CD & Automation           |    10% |
| Documentation & Presentation |     5% |

---

# Optional Advanced Challenges

Participants seeking additional challenge can implement one or more of the following:

* Multi-model endpoints for serving multiple churn models.
* Canary or shadow deployments before full production rollout.
* Cost optimization using Serverless Inference or asynchronous inference.
* Custom Docker containers for training and inference.
* Multi-account deployment (development, staging, production).
* Infrastructure as Code using AWS CloudFormation or Terraform.
* Integration with Amazon QuickSight for executive dashboards.
* Real-time event ingestion using Amazon Kinesis or Amazon MSK.
* Feature lineage and metadata tracking across the MLOps lifecycle.

---

# Final Learning Outcomes

After completing this capstone, participants will have demonstrated the ability to:

* Translate business requirements into an AI solution architecture.
* Build and operationalize an end-to-end machine learning platform on AWS.
* Apply MLOps best practices for governance, automation, monitoring, and continuous improvement.
* Deliver a production-ready, scalable, and maintainable customer churn prediction solution suitable for enterprise environments.

This capstone serves as a comprehensive demonstration of the complete AWS SageMaker MLOps lifecycle and provides a portfolio-quality project that reflects real-world enterprise AI implementation practices.
