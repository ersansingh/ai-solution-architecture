# Phase 1 – AWS Environment Setup

## Lab Guide: Preparing the AWS SageMaker Environment

**Lab Duration:** 45–60 Minutes

**Objective:**
Prepare a production-ready AWS environment for building, training, deploying, and monitoring machine learning models using the SageMaker ecosystem.

---

# Learning Objectives

By the end of this phase, participants will be able to:

* Understand the AWS services used throughout the lab.
* Create and organize an Amazon S3 bucket for the ML lifecycle.
* Configure AWS IAM permissions securely.
* Launch and configure Amazon SageMaker Studio.
* Verify that the environment is ready for model development.
* Understand the overall SageMaker architecture.

---

# AWS Services Used

| Service                 | Purpose                                              |
| ----------------------- | ---------------------------------------------------- |
| Amazon S3               | Data Lake for datasets, model artifacts, predictions |
| Amazon SageMaker Studio | ML development environment                           |
| AWS IAM                 | Identity and access management                       |
| Amazon ECR              | Store custom Docker images (optional later)          |
| CloudWatch              | Logging and monitoring                               |
| AWS Step Functions      | Workflow orchestration (later phases)                |
| EventBridge             | Scheduled retraining (later phases)                  |
| SageMaker               | Training and deployment                              |

---

# Architecture

```text
                     AWS Account
                          │
                          ▼
                Amazon SageMaker Studio
                          │
                          │
            ┌─────────────┼───────────────┐
            │             │               │
            ▼             ▼               ▼
       Amazon S3     SageMaker       CloudWatch
         Bucket       Notebook          Logs
            │
            ▼
      Raw Data
      Processed Data
      Models
      Predictions
```

---

# Prerequisites

Participants should have:

* AWS Account
* Administrator or SageMaker Full Access
* Internet Browser
* AWS Region selected (Recommended: us-east-1 or ap-south-1)

---

# Task 1 – Select AWS Region

## Why?

AWS services are regional.

Using the same region avoids latency and permission issues.

Recommended:

* us-east-1
* us-east-2
* eu-west-1
* ap-south-1

---

### Steps

1. Login to AWS Console.
2. Click the Region selector.
3. Choose your lab region.

---

Expected Result

All future services will be created in the same region.

---

# Task 2 – Create Amazon S3 Bucket

## Why?

Amazon S3 will act as the enterprise Data Lake.

Everything in this lab is stored here:

* Raw Data
* Cleaned Data
* Features
* Training Data
* Models
* Predictions
* Logs

---

### Naming Convention

Use a globally unique name.

Example

```text
teleconnect-churn-<yourname>-lab
```

Example

```text
teleconnect-churn-john-lab
```

---

### Steps

Navigate to

AWS Console

↓

Amazon S3

↓

Create Bucket

---

Bucket Settings

| Property            | Value                          |
| ------------------- | ------------------------------ |
| Bucket Name         | teleconnect-churn-yourname-lab |
| Region              | Same as SageMaker              |
| Block Public Access | Enabled                        |
| Versioning          | Enabled                        |
| Encryption          | SSE-S3                         |

---

Click

Create Bucket

---

Expected Result

A new S3 bucket appears.

---

# Task 3 – Create Folder Structure

Inside the bucket create folders.

```text
raw-data/

processed-data/

feature-store/

training/

models/

predictions/

monitoring/

pipeline/

scripts/

notebooks/

artifacts/

logs/
```

---

## Why each folder?

### raw-data/

Original CSV files

Never modified.

---

### processed-data/

Clean datasets.

---

### feature-store/

Feature exports.

---

### training/

Training datasets.

---

### models/

Model artifacts (.tar.gz)

---

### predictions/

Batch predictions.

---

### monitoring/

Monitoring reports.

---

### pipeline/

Pipeline definitions.

---

### scripts/

Training scripts.

---

### notebooks/

Jupyter notebooks.

---

### artifacts/

Evaluation reports.

---

### logs/

Application logs.

---

Expected Result

A structured Data Lake.

---

# Task 4 – Create IAM Role

## Why?

SageMaker needs permission to access AWS resources.

---

Navigate

IAM

↓

Roles

↓

Create Role

---

Trusted Entity

AWS Service

↓

SageMaker

---

Attach Policies

Recommended

* AmazonSageMakerFullAccess
* AmazonS3FullAccess *(lab only; in production, use least privilege)*
* CloudWatchFullAccess

Optional

* AmazonECRFullAccess

---

Role Name

```text
SageMakerExecutionRole
```

---

Expected Result

IAM Role created.

---

# Task 5 – Launch SageMaker Studio

Navigate

AWS Console

↓

Amazon SageMaker

↓

Studio

↓

Create Domain

---

Quick Setup

Recommended for training.

---

Authentication

IAM

---

Select

Execution Role

↓

SageMakerExecutionRole

---

Click

Create

---

Wait

Approximately

5–10 minutes.

---

Expected Result

Studio launches successfully.

---

# Task 6 – Create Notebook

Inside Studio

File

↓

New

↓

Notebook

---

Kernel

Python 3

---

Notebook Name

```text
Customer_Churn_Lab.ipynb
```

---

Expected Result

Notebook opens.

---

# Task 7 – Verify Python Environment

Run

```python
print("Hello SageMaker!")
```

Expected Output

```text
Hello SageMaker!
```

---

# Task 8 – Install Required Libraries

Run

```python
%pip install \
sagemaker \
boto3 \
pandas \
numpy \
matplotlib \
seaborn \
scikit-learn \
xgboost \
shap
```

---

Why?

| Library   | Purpose              |
| --------- | -------------------- |
| pandas    | Data processing      |
| numpy     | Numerical operations |
| boto3     | AWS SDK              |
| sagemaker | SageMaker SDK        |
| sklearn   | Machine Learning     |
| xgboost   | Gradient Boosting    |
| shap      | Explainability       |

---

Expected Result

Libraries installed.

---

# Task 9 – Verify AWS SDK

Run

```python
import boto3

session = boto3.Session()

print(session.region_name)
```

Expected Output

```text
ap-south-1
```

(or your selected region)

---

# Task 10 – Verify SageMaker SDK

Run

```python
import sagemaker

print(sagemaker.__version__)
```

Expected Result

Latest SDK version.

---

# Task 11 – Verify Execution Role

Run

```python
import sagemaker

role = sagemaker.get_execution_role()

print(role)
```

Expected Output

```text
arn:aws:iam::xxxxxxxxxxxx:role/SageMakerExecutionRole
```

---

# Task 12 – Verify S3 Access

Run

```python
import boto3

s3 = boto3.client("s3")

response = s3.list_buckets()

for bucket in response["Buckets"]:
    print(bucket["Name"])
```

Expected Result

Your S3 bucket is listed.

---

# Task 13 – Define Project Variables

Create a configuration cell in the notebook:

```python
import sagemaker

session = sagemaker.Session()

bucket = "teleconnect-churn-yourname-lab"

region = session.boto_region_name

prefix = "customer-churn"

print(bucket)
print(region)
```

---

Expected Result

Project variables initialized.

---

# Task 14 – Test Upload to S3

Create a small DataFrame and upload it.

```python
import pandas as pd

df = pd.DataFrame({
    "id":[1,2],
    "value":[100,200]
})

df.to_csv("test.csv", index=False)

session.upload_data(
    "test.csv",
    bucket=bucket,
    key_prefix="raw-data"
)
```

---

Expected Result

Navigate to the S3 bucket and confirm that `test.csv` appears under the `raw-data/` folder.

---

# Task 15 – Verify End-to-End Connectivity

Run the following checklist:

| Validation                   | Expected Outcome |
| ---------------------------- | ---------------- |
| AWS Region selected          | ✓                |
| S3 bucket created            | ✓                |
| Folder structure created     | ✓                |
| IAM role attached            | ✓                |
| SageMaker Studio launched    | ✓                |
| Notebook created             | ✓                |
| Python kernel working        | ✓                |
| Required libraries installed | ✓                |
| SageMaker SDK available      | ✓                |
| Execution role detected      | ✓                |
| S3 upload successful         | ✓                |

---

# Common Issues and Troubleshooting

| Issue                                       | Possible Cause                           | Resolution                                            |
| ------------------------------------------- | ---------------------------------------- | ----------------------------------------------------- |
| `AccessDenied` when accessing S3            | Missing IAM permissions                  | Verify the execution role includes S3 access          |
| `get_execution_role()` fails                | Notebook not running in SageMaker Studio | Use SageMaker Studio or provide the role ARN manually |
| Bucket name already exists                  | S3 bucket names are globally unique      | Choose a unique bucket name                           |
| `ModuleNotFoundError: sagemaker`            | SDK not installed                        | Install with `%pip install sagemaker`                 |
| SageMaker Studio takes a long time to start | Domain creation in progress              | Wait a few minutes and refresh the console            |

---

# Deliverables for Phase 1

At the end of this phase, participants should have:

* An AWS account configured in a single region.
* A secure Amazon S3 bucket with the required folder structure.
* A SageMaker execution IAM role with appropriate permissions.
* A working SageMaker Studio environment.
* A Jupyter notebook configured with the necessary Python libraries.
* Verified connectivity to Amazon S3 and SageMaker.

