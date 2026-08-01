# Hands-on Lab: Customer Churn Prediction Using the AWS SageMaker Model Training & Serving Ecosystem

## Lab Overview

In this lab, participants will build an end-to-end machine learning solution using the **AWS SageMaker ecosystem**. They will prepare data, engineer features, train multiple machine learning models, track experiments, register the best-performing model, deploy it as a scalable inference endpoint, and monitor model performance.

The lab simulates a real enterprise MLOps workflow followed by organizations deploying AI solutions in production.

---

# Business Scenario

**TeleConnect**, a global telecommunications company serving over 30 million customers across North America and Europe, has observed an increasing number of customers discontinuing their subscriptions.

Every 1% increase in churn results in approximately **$25 million annual revenue loss**.

Currently, retention teams rely on manually generated reports and static business rules, which often identify customers only after they have already decided to leave.

The executive leadership wants to implement an AI-powered prediction system capable of identifying customers likely to churn within the next **90 days** so that proactive retention campaigns can be launched.

The solution must support both **batch predictions** for marketing campaigns and **real-time predictions** during customer support interactions.

---

# Business Objectives

Design an end-to-end machine learning solution capable of:

* Predicting customer churn probability
* Identifying important churn factors
* Deploying a production-grade inference service
* Supporting continuous model improvement
* Monitoring prediction quality over time

---

# Business Success Criteria

The business has defined the following KPIs.

| KPI                         | Target                              |
| --------------------------- | ----------------------------------- |
| ROC AUC                     | > 0.90                              |
| Precision                   | >85%                                |
| Recall                      | >80%                                |
| Batch prediction time       | <30 minutes for 5 million customers |
| Real-time inference latency | <150 ms                             |
| Endpoint availability       | 99.9%                               |
| Monthly retraining          | Automated                           |

---

# Available Data Sources

Participants are provided with the following datasets.

### Customer Profile

* Customer ID
* Age
* Gender
* Region
* Customer Segment
* Tenure

---

### Billing Data

* Monthly Charges
* Total Charges
* Payment Method
* Outstanding Balance
* Contract Type

---

### Service Usage

* Internet Package
* Voice Usage
* Data Usage
* Roaming Usage
* Number of Support Calls
* Streaming Services

---

### Customer Support

* Number of Tickets
* Average Resolution Time
* Complaint Count
* Satisfaction Score

---

### Churn Label

* Churn (Yes/No)

---

# Dataset Characteristics

| Property            | Value                    |
| ------------------- | ------------------------ |
| Total Records       | 2,500,000                |
| Features            | 48                       |
| Label               | Binary Classification    |
| Missing Values      | Yes                      |
| Categorical Columns | 12                       |
| Numerical Columns   | 36                       |
| Class Distribution  | 82% No Churn / 18% Churn |

---

# AWS Environment

Participants have access to the following AWS resources.

```
AWS Account

Amazon S3
    ├── Raw Data
    ├── Processed Data
    ├── Feature Store Export
    ├── Model Artifacts
    └── Batch Predictions

AWS SageMaker Studio

IAM Role

Amazon ECR

CloudWatch

EventBridge

AWS Lambda

Amazon API Gateway

Amazon SNS

AWS Step Functions
```

---

# AWS Services to Use

Participants are expected to use:

* Amazon S3
* SageMaker Studio
* SageMaker Processing Jobs
* SageMaker Data Wrangler
* SageMaker Feature Store
* SageMaker Training Jobs
* SageMaker Experiments
* SageMaker Debugger
* SageMaker Clarify
* SageMaker Model Registry
* SageMaker Pipelines
* SageMaker Endpoints
* SageMaker Batch Transform
* CloudWatch
* EventBridge

---

# Technical Requirements

The solution should:

* Follow MLOps best practices
* Use infrastructure already provided
* Store all datasets in Amazon S3
* Track all experiments
* Version every trained model
* Support CI/CD deployment
* Use Auto Scaling inference endpoints
* Enable model monitoring

---

# Lab Tasks

## Part 1 – Data Exploration

Using SageMaker Studio:

* Load customer dataset from S3
* Explore missing values
* Identify skewed features
* Detect outliers
* Analyze churn distribution
* Generate feature statistics

---

## Part 2 – Data Preparation

Using SageMaker Processing Jobs or Data Wrangler:

* Handle missing values
* Encode categorical variables
* Normalize numerical features
* Remove duplicate records
* Split train/validation/test datasets
* Store processed datasets in Amazon S3

---

## Part 3 – Feature Engineering

Create new features including:

* Average Monthly Spend
* Customer Lifetime Value
* Support Frequency
* Usage Growth Rate
* Complaint Ratio
* Payment Delay Score
* Customer Risk Score

Store engineered features in:

**Amazon SageMaker Feature Store**

---

## Part 4 – Model Training

Train the following algorithms using SageMaker Training Jobs.

### Model 1

XGBoost

---

### Model 2

LightGBM (Custom Container)

---

### Model 3

Random Forest (Scikit-learn)

---

### Model 4

Linear Learner

---

### Optional

AutoML (SageMaker Autopilot)

---

Track all runs using:

* SageMaker Experiments

---

## Part 5 – Hyperparameter Tuning

Optimize:

* Learning Rate
* Tree Depth
* Number of Trees
* Minimum Child Weight
* Gamma
* Regularization

Use:

**SageMaker Hyperparameter Tuning Jobs**

---

## Part 6 – Model Evaluation

Evaluate using:

* Accuracy
* Precision
* Recall
* F1 Score
* ROC AUC
* PR Curve
* Confusion Matrix

Generate:

* Feature Importance
* SHAP Values
* Explainability Report

Use:

* SageMaker Clarify

---

## Part 7 – Model Debugging

Use:

* SageMaker Debugger

Identify:

* Overfitting
* Gradient Explosion
* Poor Convergence
* Dead Features

---

## Part 8 – Register Best Model

Register model into:

**SageMaker Model Registry**

Include:

* Metrics
* Version
* Metadata
* Approval Status

---

## Part 9 – Model Deployment

Deploy using:

Real-Time Endpoint

Requirements:

* Auto Scaling
* Multiple Instances
* Rolling Deployment
* Health Checks

---

## Part 10 – Batch Inference

Generate predictions for:

5 million customers

Store results in:

Amazon S3

---

## Part 11 – API Integration

Expose prediction endpoint using:

```
Client

↓

API Gateway

↓

Lambda

↓

SageMaker Endpoint

↓

Prediction Response
```

---

## Part 12 – Model Monitoring

Configure:

* Data Drift Monitoring
* Model Quality Monitoring
* Feature Drift Detection
* Prediction Distribution
* Endpoint Latency
* Endpoint Errors

Use:

* SageMaker Model Monitor
* Amazon CloudWatch

---

## Part 13 – Automated Retraining Pipeline

Create a SageMaker Pipeline that:

```
New Data Arrives

↓

Processing Job

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

↓

Monitoring
```

Trigger retraining using:

* Amazon EventBridge (scheduled monthly)
* S3 Event Notifications (new training data)

---

# Expected Deliverables

At the end of the lab, participants should produce:

1. Data exploration report
2. Feature engineering notebook
3. Trained ML models
4. Hyperparameter tuning results
5. Experiment tracking dashboard
6. Model explainability report
7. Registered model in SageMaker Model Registry
8. Real-time inference endpoint
9. Batch prediction output
10. API endpoint for online inference
11. CloudWatch monitoring dashboard
12. Automated SageMaker Pipeline for retraining

---

# AWS SageMaker Architecture Flow

```text
                  Customer Data
                        │
                        ▼
                 Amazon S3 (Raw Data)
                        │
                        ▼
          SageMaker Processing / Data Wrangler
                        │
                        ▼
            SageMaker Feature Store
                        │
                        ▼
             SageMaker Training Jobs
                        │
                        ▼
            SageMaker Experiments
                        │
                        ▼
     Hyperparameter Tuning + Debugger + Clarify
                        │
                        ▼
             SageMaker Model Registry
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
  Real-Time Endpoint          Batch Transform
          │                           │
          ▼                           ▼
 API Gateway → Lambda          Amazon S3 Predictions
          │
          ▼
      Client Applications
                        │
                        ▼
        CloudWatch + Model Monitor
                        │
                        ▼
            SageMaker Pipelines
                        │
                        ▼
           Automated Retraining
```

## Learning Outcomes

By completing this lab, participants will gain hands-on experience with the complete AWS SageMaker MLOps lifecycle, including:

* Data preparation with SageMaker Processing and Data Wrangler
* Centralized feature management using SageMaker Feature Store
* Training and tuning multiple ML algorithms
* Experiment tracking and model debugging
* Model explainability with SageMaker Clarify
* Model versioning and governance using Model Registry
* Production deployment with real-time endpoints and batch inference
* Operational monitoring using CloudWatch and Model Monitor
* Automated retraining using SageMaker Pipelines and EventBridge

This lab closely mirrors the workflow used by enterprise teams to build, deploy, and operate production-grade machine learning systems on AWS.
