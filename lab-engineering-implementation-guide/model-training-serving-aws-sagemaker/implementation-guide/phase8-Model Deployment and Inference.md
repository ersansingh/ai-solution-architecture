# Phase 8 – Model Deployment and Inference

## Lab Guide: Deploying Production Models with Amazon SageMaker Endpoints and Batch Transform

**Lab Duration:** **3–3.5 Hours**

---

# Phase Objective

By the end of Phase 7, participants have:

* Built multiple models
* Tuned hyperparameters
* Evaluated model performance
* Generated explainability reports
* Registered and approved the model in SageMaker Model Registry

The next step is to make the model available for real-world applications.

In this phase, participants will deploy the approved model using the Amazon SageMaker hosting ecosystem and learn how enterprise organizations expose AI models as scalable production services.

Participants will implement:

* Real-Time Inference
* Batch Inference
* Auto Scaling
* API Integration
* Endpoint Monitoring
* Blue/Green Deployment Concepts

---

# Learning Objectives

By the end of this phase, participants will be able to:

* Deploy models from SageMaker Model Registry.
* Create production-grade SageMaker Endpoints.
* Configure endpoint auto scaling.
* Invoke endpoints programmatically.
* Deploy REST APIs using API Gateway and Lambda.
* Run large-scale Batch Transform jobs.
* Compare online and offline inference architectures.
* Understand production deployment strategies.

---

# Enterprise Architecture

```text
                          SageMaker Model Registry
                                      │
                                      ▼
                           Approved Model Version
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
          Real-Time Endpoint                  Batch Transform
                     │                                 │
                     ▼                                 ▼
          API Gateway + Lambda                Batch Prediction
                     │                                 │
                     ▼                                 ▼
          Web / Mobile Apps                Marketing / Analytics
                     │                                 │
                     └────────────────┬────────────────┘
                                      ▼
                              CloudWatch Logs
```

---

# Enterprise Deployment Workflow

```text
Training
     │
     ▼
Evaluation
     │
     ▼
Model Registry
     │
     ▼
Approval
     │
     ▼
Production Endpoint
     │
     ▼
Applications
```

---

# Why Deployment Matters

Training a model creates a **model artifact**.

Deployment transforms that artifact into a **production service** capable of answering prediction requests.

Example:

Customer logs into the telecom portal.

↓

Customer profile is sent to SageMaker.

↓

Model predicts

```text
Churn Probability = 94%
```

↓

Retention offer is generated immediately.

---

# Input

From Phase 7

```text
Approved Model

Model Registry

Training Artifacts
```

---

# Expected Output

```text
Real-Time Endpoint

Batch Prediction Job

REST API

Auto Scaling Configuration

Prediction Results
```

---

# Task 1 – Review the Registered Model

Navigate

```text
Amazon SageMaker

↓

Model Registry
```

Verify

* Approved status
* Model version
* Artifacts
* Metrics

Discussion

Why deploy only approved models?

---

# Task 2 – Create a SageMaker Model

Load the approved model.

Example

```python
from sagemaker.model import Model

model = Model(
    image_uri=xgb.image_uri,
    model_data=xgb.model_data,
    role=role
)
```

Discussion

Explain

Model

↓

Endpoint Configuration

↓

Endpoint

---

# Task 3 – Deploy a Real-Time Endpoint

Deploy

```python
predictor = model.deploy(

instance_type="ml.m5.large",

initial_instance_count=1

)
```

Expected Result

SageMaker provisions

* EC2 instance
* Container
* Endpoint

Deployment time

Approximately

5–10 minutes

---

# Task 4 – Understand Endpoint Components

```text
                 Client
                   │
                   ▼
           SageMaker Endpoint
                   │
          ┌────────┴────────┐
          ▼                 ▼
   Model Container      Model Artifact
```

Discussion

Difference between

* Endpoint
* Endpoint Configuration
* Model

---

# Task 5 – Invoke the Endpoint

Example request

```python
sample = X_test.iloc[0:1]

predictor.predict(sample.values)
```

Expected Output

```text
0.94
```

Discussion

What does

0.94

mean?

It represents

94% probability of churn.

---

# Task 6 – Invoke Using SageMaker Runtime

Enterprise applications rarely use notebooks.

Instead they call

```text
SageMaker Runtime API
```

Example

```python
runtime = boto3.client("sagemaker-runtime")
```

Invoke

```python
response = runtime.invoke_endpoint(

EndpointName="customer-churn",

ContentType="text/csv",

Body=payload

)
```

Discussion

Why use Runtime API?

---

# Task 7 – Build REST API

Architecture

```text
Client

↓

API Gateway

↓

Lambda

↓

SageMaker Endpoint
```

---

# Task 8 – Create Lambda Function

Lambda receives

```json
{
  "age":42,
  "monthly_charge":98,
  "support_calls":6
}
```

Lambda

↓

Calls SageMaker

↓

Returns

```json
{
   "prediction":"Likely to Churn",

   "probability":0.93
}
```

Discussion

Why use Lambda?

* Authentication
* Business Logic
* Logging
* Validation

---

# Task 9 – Create API Gateway

Configure

```text
POST

/predict
```

Integration

↓

Lambda

Expected Result

External applications can invoke

```text
https://xxxxx.execute-api.amazonaws.com/predict
```

---

# Task 10 – Test REST API

Use

* Postman
* curl
* Python requests

Example

```json
{
  "age":51,
  "monthly_charge":89,
  "support_calls":7
}
```

Expected Output

```json
{
   "prediction":"Likely to Churn",

   "probability":0.91
}
```

Discussion

Why expose APIs instead of direct endpoint access?

---

# Task 11 – Configure Auto Scaling

Navigate

```text
SageMaker

↓

Endpoints

↓

Auto Scaling
```

Configure

Minimum Instances

```text
1
```

Maximum Instances

```text
5
```

Target Metric

```text
InvocationsPerInstance
```

Discussion

Why Auto Scaling?

* Cost optimization
* Handle traffic spikes
* Maintain latency

---

# Task 12 – Batch Transform

Business Requirement

Marketing needs churn scores for

```text
5 Million Customers
```

Real-time inference is unnecessary.

Use

Batch Transform.

Input

```text
batch/customers.csv
```

Output

```text
predictions/output.csv
```

Discussion

When should Batch Transform be preferred?

---

# Task 13 – Launch Batch Transform Job

Example

```python
transformer = xgb.transformer(

instance_count=1,

instance_type="ml.m5.large",

output_path=f"s3://{bucket}/predictions"
)
```

Execute

```python
transformer.transform(

data=train_path,

content_type="text/csv"

)

transformer.wait()
```

---

Expected Result

Predictions stored in Amazon S3.

---

# Task 14 – Review Batch Predictions

Navigate

```text
Amazon S3

↓

predictions/
```

Example

```text
Customer ID

Prediction

Probability
```

Discussion

How can marketing use these predictions?

---

# Task 15 – Compare Real-Time vs Batch

| Feature    | Real-Time Endpoint  | Batch Transform     |
| ---------- | ------------------- | ------------------- |
| Response   | Milliseconds        | Minutes/Hours       |
| Scale      | Individual requests | Millions of records |
| Cost       | Always running      | Pay per job         |
| Example    | Customer portal     | Marketing campaign  |
| Latency    | Low                 | High                |
| Throughput | Moderate            | Very High           |

---

# Task 16 – Blue/Green Deployment

Explain

```text
Current Endpoint

↓

New Endpoint

↓

Traffic Shift

↓

Validation

↓

Production
```

Discussion

Benefits

* Zero downtime
* Safe deployment
* Easy rollback

---

# Task 17 – A/B Testing

Example

```text
Model V1

50%

Model V2

50%
```

Compare

* Accuracy
* Latency
* Customer retention

Discussion

When should A/B testing be used?

---

# Task 18 – Cost Optimization

Discuss endpoint choices.

| Instance     | Use Case          |
| ------------ | ----------------- |
| ml.t3.medium | Development       |
| ml.m5.large  | Production CPU    |
| ml.c5.xlarge | Compute intensive |
| ml.g5.xlarge | GPU inference     |

Discussion

How does instance selection affect cost?

---

# Best Practices

* Deploy only approved models from Model Registry.
* Use Auto Scaling for production endpoints.
* Validate all API requests before invoking the endpoint.
* Secure endpoints using IAM or Amazon Cognito.
* Prefer Batch Transform for periodic large-scale predictions.
* Use blue/green deployments to reduce deployment risk.
* Monitor endpoint health continuously with CloudWatch.

---

# Deliverables

Participants should submit:

1. Screenshot of the deployed SageMaker Endpoint.
2. Endpoint configuration details.
3. Sample inference notebook.
4. Lambda function code.
5. API Gateway configuration.
6. Example REST API request and response.
7. Batch Transform job screenshot.
8. Batch prediction output in Amazon S3.
9. Comparison of real-time and batch inference.

---

# Validation Checklist

| Validation                | Expected Result |
| ------------------------- | --------------- |
| Model deployed            | ✓               |
| Endpoint running          | ✓               |
| Predictions returned      | ✓               |
| Runtime API working       | ✓               |
| Lambda configured         | ✓               |
| API Gateway working       | ✓               |
| Batch Transform completed | ✓               |
| Predictions stored in S3  | ✓               |
| Auto Scaling enabled      | ✓               |

---

# Discussion Questions

1. When should you use a real-time endpoint instead of Batch Transform?
2. Why is API Gateway typically placed in front of SageMaker Endpoints?
3. What business scenarios benefit from Batch Transform?
4. How does Auto Scaling improve both performance and cost efficiency?
5. What are the advantages of blue/green deployments over replacing an endpoint directly?
6. How would you secure a production inference API exposed to external clients?

---

# Transition to Phase 9

By the end of this phase, participants have a fully functional inference solution capable of serving predictions in both **real-time** and **batch** modes. However, deployment is only the beginning of an ML system's lifecycle.

In **Phase 9 – Model Monitoring, Data Drift Detection, and Automated Retraining**, participants will learn how to:

* Monitor endpoint health with **Amazon CloudWatch**.
* Detect **data quality issues** and **feature drift** using **Amazon SageMaker Model Monitor**.
* Measure prediction quality over time.
* Build an automated retraining pipeline using **Amazon SageMaker Pipelines** and **Amazon EventBridge** to continuously improve the model as new data becomes available.

This final phase completes the end-to-end enterprise MLOps lifecycle on AWS SageMaker.
