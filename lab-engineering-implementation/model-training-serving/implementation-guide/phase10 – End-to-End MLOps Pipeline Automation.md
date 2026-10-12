# Phase 10 – End-to-End MLOps Pipeline Automation (CI/CD)

## Implementation Guide: Building an Automated Production MLOps Pipeline with AWS

**Lab Duration:** **3–4 Hours**

---

# Phase Objective

In the previous phases, participants manually:

* Uploaded datasets
* Trained models
* Evaluated models
* Registered models
* Deployed endpoints
* Configured monitoring

In a production environment, these activities should be **automated** using CI/CD and infrastructure-as-code principles.

In this phase, participants will build a complete automated MLOps pipeline that:

* Detects new training data
* Executes a SageMaker Pipeline
* Registers the model
* Performs automated quality checks
* Requests approval
* Deploys to staging
* Promotes to production after validation
* Notifies stakeholders

---

# Learning Objectives

By the end of this phase, participants will be able to:

* Build an end-to-end MLOps workflow.
* Automate model deployment using CI/CD.
* Integrate GitHub with AWS.
* Use CodePipeline or GitHub Actions.
* Implement approval gates.
* Deploy using Blue/Green strategies.
* Roll back failed deployments.

---

# Enterprise Architecture

```text
                GitHub Repository
                        │
                        ▼
              GitHub Actions / CodePipeline
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
    Infrastructure                Source Code
      Validation                  Unit Tests
          │                           │
          └─────────────┬─────────────┘
                        ▼
               SageMaker Pipeline
                        │
                        ▼
                Model Evaluation
                        │
                        ▼
              SageMaker Model Registry
                        │
              Manual Approval Gate
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
      Staging Endpoint       Production Endpoint
            │                       │
            ▼                       ▼
      Smoke Tests          Blue/Green Deployment
            │                       │
            ▼                       ▼
        CloudWatch           Business Applications
```

---

# Repository Structure

Create the following Git repository:

```text
customer-churn-mlops/

├── notebooks/
├── src/
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── train.py
│   ├── evaluate.py
│   ├── inference.py
│   └── utils.py
│
├── pipelines/
│   └── pipeline.py
│
├── deployment/
│   ├── endpoint.py
│   ├── autoscaling.py
│   └── monitoring.py
│
├── tests/
├── config/
├── requirements.txt
└── README.md
```

---

# Task 1 – Store Source Code in Git

## Objective

Version control all ML assets.

Commit:

* Training code
* Evaluation code
* Pipeline definition
* Configuration files

Example:

```bash
git init
git add .
git commit -m "Initial MLOps pipeline"
```

---

# Task 2 – Configure GitHub Actions

Create:

```text
.github/workflows/mlops.yml
```

Example workflow:

```yaml
name: Customer Churn MLOps

on:
  push:
    branches:
      - main

jobs:

  validate:
    runs-on: ubuntu-latest

    steps:

    - uses: actions/checkout@v4

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Run unit tests
      run: pytest tests/

    - name: Lint
      run: flake8 src/
```

---

# Task 3 – Trigger SageMaker Pipeline

Use the AWS CLI or SDK within the CI workflow.

Example:

```bash
aws sagemaker start-pipeline-execution \
  --pipeline-name CustomerChurnPipeline
```

Expected Result:

The SageMaker Pipeline starts automatically after code is merged.

---

# Task 4 – Validate Model Quality

Configure quality gates.

Example thresholds:

| Metric    | Minimum |
| --------- | ------- |
| Accuracy  | 90%     |
| Precision | 85%     |
| Recall    | 80%     |
| ROC AUC   | 0.90    |

If thresholds are not met:

```text
Pipeline Status

FAILED
```

No deployment occurs.

---

# Task 5 – Register the Model

Automatically register successful models.

Metadata should include:

* Model version
* Dataset version
* Git commit ID
* Training timestamp
* Evaluation metrics

Expected Result:

```text
Customer-Churn-Models

Version 7

Pending Approval
```

---

# Task 6 – Manual Approval

Before production deployment:

Reviewer checks:

* Evaluation metrics
* Explainability report
* Bias report
* Monitoring history

Approval options:

```text
Approve

Reject
```

Discussion:

Why should production deployment require human approval?

---

# Task 7 – Deploy to Staging

Deploy the approved model to:

```text
customer-churn-staging
```

Perform smoke tests:

* Endpoint available
* Prediction returned
* Latency acceptable

---

# Task 8 – Blue/Green Deployment

Deploy a new production version without downtime.

Workflow:

```text
Production Endpoint (Blue)
          │
          ▼
Deploy Green Endpoint
          │
          ▼
Run Validation Tests
          │
          ▼
Shift 10% Traffic
          │
          ▼
Shift 50% Traffic
          │
          ▼
Shift 100% Traffic
```

Rollback if validation fails.

---

# Task 9 – Configure Monitoring

Automatically:

* Enable Data Capture
* Configure Model Monitor
* Create CloudWatch Dashboard
* Create CloudWatch Alarms
* Configure SNS notifications

---

# Task 10 – Automated Rollback

Define rollback criteria.

Example:

| Metric              | Threshold |
| ------------------- | --------- |
| Error Rate          | >5%       |
| Latency             | >300 ms   |
| Prediction failures | >2%       |

If exceeded:

```text
Production V8

↓

Rollback

↓

Production V7
```

---

# Task 11 – End-to-End Validation

Execute the complete workflow:

1. Commit a code change.
2. Push to the `main` branch.
3. GitHub Actions runs tests.
4. SageMaker Pipeline starts.
5. Model is trained and evaluated.
6. Model is registered.
7. Manual approval is completed.
8. Model is deployed to staging.
9. Smoke tests pass.
10. Blue/Green deployment promotes the model to production.
11. Monitoring and alarms become active.

---

# Deliverables

Participants should provide:

1. GitHub repository with complete source code.
2. GitHub Actions workflow (or AWS CodePipeline equivalent).
3. SageMaker Pipeline execution history.
4. Model Registry with version history.
5. Staging and production endpoint details.
6. CloudWatch dashboard and alarm configuration.
7. Documentation describing the CI/CD process.
8. Evidence of a successful rollback test.

---

# Validation Checklist

| Validation                       | Expected Result |
| -------------------------------- | --------------- |
| Source code versioned            | ✓               |
| CI workflow executes             | ✓               |
| Unit tests pass                  | ✓               |
| SageMaker Pipeline triggered     | ✓               |
| Model quality gate enforced      | ✓               |
| Model registered                 | ✓               |
| Manual approval completed        | ✓               |
| Staging deployment successful    | ✓               |
| Blue/Green deployment successful | ✓               |
| Monitoring configured            | ✓               |
| Rollback procedure validated     | ✓               |

---

# Discussion Questions

1. Why should ML pipelines be integrated with source control?
2. How do CI/CD pipelines reduce deployment risk?
3. Why are automated quality gates important before model promotion?
4. What advantages does Blue/Green deployment offer over in-place updates?
5. Under what conditions should an automatic rollback occur?
6. How do CI/CD, Model Registry, SageMaker Pipelines, and Model Monitor work together to support enterprise MLOps?

---

# Final Capstone

Participants should demonstrate a complete enterprise workflow:

1. Modify the training code or add new training data.
2. Push the change to the Git repository.
3. Observe automatic CI validation.
4. Trigger the SageMaker Pipeline.
5. Review model evaluation results.
6. Approve the new model version.
7. Deploy to staging and then production using Blue/Green deployment.
8. Verify inference through the production API.
9. Confirm monitoring, alarms, and rollback mechanisms are operational.

This phase completes the transformation from a manually executed ML workflow to a fully automated, production-ready MLOps platform aligned with enterprise best practices.
