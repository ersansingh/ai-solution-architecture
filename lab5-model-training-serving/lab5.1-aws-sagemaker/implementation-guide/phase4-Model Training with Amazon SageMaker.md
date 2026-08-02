# Phase 4 – Model Training with Amazon SageMaker

## Lab Guide: Training Multiple Machine Learning Models Using the SageMaker Ecosystem

**Lab Duration:** **2.5–3 Hours**

---

# Phase Objective

In this phase, participants will build and compare multiple machine learning models using **Amazon SageMaker Training Jobs**. Rather than training models locally in the notebook, they will learn how enterprise organizations execute scalable, managed training workloads on AWS.

Participants will:

* Configure SageMaker training jobs
* Train multiple ML algorithms
* Store model artifacts in Amazon S3
* Track training metrics
* Compare model performance
* Understand the trade-offs between different algorithms

This phase simulates the workflow followed by ML Engineers in production environments.

---

# Learning Objectives

By the end of this phase, participants will be able to:

* Understand SageMaker managed training.
* Configure training jobs using the SageMaker Python SDK.
* Select suitable algorithms for binary classification.
* Launch multiple training jobs.
* Monitor training progress.
* Compare model performance.
* Store model artifacts for deployment.
* Understand distributed and managed training concepts.

---

# Architecture

```text
                   Training Dataset
                          │
                          ▼
                   Amazon S3
                          │
                          ▼
               SageMaker Training Job
                          │
        ┌─────────────────┼───────────────────┐
        ▼                 ▼                   ▼
   XGBoost          Linear Learner      Scikit-Learn
        │                 │                   │
        └─────────────────┼───────────────────┘
                          ▼
                Model Artifacts (.tar.gz)
                          │
                          ▼
                     Amazon S3 Models
```

---

# Algorithms Used

Participants will train four models.

| Model          | Framework        | SageMaker Support |
| -------------- | ---------------- | ----------------- |
| XGBoost        | Built-in         | Native            |
| Linear Learner | Built-in         | Native            |
| Random Forest  | Scikit-Learn     | Managed Container |
| LightGBM       | Custom Container | BYOC (optional)   |

For this lab, XGBoost, Linear Learner, and Random Forest are mandatory. LightGBM can be included as an advanced exercise.

---

# Input Data

Training files created in Phase 3.

```text
training/

train.csv

validation.csv

test.csv
```

---

# Expected Output

```text
models/

xgboost/

linear-learner/

random-forest/

lightgbm/
```

Each folder will contain:

```text
model.tar.gz
```

---

# Task 1 – Review the Training Dataset

## Objective

Verify that the data is ready for training.

Load the training dataset.

```python
train = pd.read_csv("train.csv")

train.head()
```

Verify:

* No missing values
* Target column exists
* Features are numeric
* Data types are correct

---

# Task 2 – Upload Training Data to Amazon S3

```python
session.upload_data(
    "train.csv",
    bucket=bucket,
    key_prefix="training"
)

session.upload_data(
    "validation.csv",
    bucket=bucket,
    key_prefix="training"
)
```

Expected structure:

```text
training/

train.csv

validation.csv
```

---

# Task 3 – Configure SageMaker Session

```python
import sagemaker
from sagemaker import Session

session = Session()

role = sagemaker.get_execution_role()
```

Verify:

```python
print(role)
```

---

# Task 4 – Define S3 Locations

```python
train_path = f"s3://{bucket}/training/train.csv"

validation_path = f"s3://{bucket}/training/validation.csv"

output_path = f"s3://{bucket}/models/"
```

---

# Task 5 – Train the XGBoost Model

## Why XGBoost?

XGBoost is one of the most popular algorithms for structured/tabular datasets because it typically offers:

* High predictive accuracy
* Robust handling of missing values
* Built-in feature importance
* Excellent performance on churn prediction problems

---

## Configure the Estimator

```python
from sagemaker.estimator import Estimator
from sagemaker.image_uris import retrieve

container = retrieve(
    framework="xgboost",
    region=session.boto_region_name,
    version="1.7-1"
)

xgb = Estimator(
    image_uri=container,
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    output_path=output_path,
    sagemaker_session=session
)
```

---

## Configure Hyperparameters

```python
xgb.set_hyperparameters(
    objective="binary:logistic",
    num_round=200,
    max_depth=6,
    eta=0.2,
    gamma=2,
    min_child_weight=5,
    subsample=0.8
)
```

Explain each hyperparameter:

| Hyperparameter   | Purpose                           |
| ---------------- | --------------------------------- |
| objective        | Binary classification             |
| num_round        | Number of boosting iterations     |
| max_depth        | Maximum tree depth                |
| eta              | Learning rate                     |
| gamma            | Minimum split loss                |
| min_child_weight | Controls overfitting              |
| subsample        | Fraction of data sampled per tree |

---

## Launch the Training Job

```python
from sagemaker.inputs import TrainingInput

xgb.fit({
    "train": TrainingInput(train_path),
    "validation": TrainingInput(validation_path)
})
```

---

Expected Result

Participants should observe:

* SageMaker creates a managed training job.
* Training logs appear in the notebook.
* Metrics stream to CloudWatch.
* Model artifacts are saved to Amazon S3.

---

# Task 6 – Monitor the Training Job

Navigate to:

```text
Amazon SageMaker

↓

Training Jobs
```

Observe:

* Training status
* Resource utilization
* Hyperparameters
* Model artifacts
* Logs

Discussion:

* What information is available during training?
* Why is monitoring important in enterprise environments?

---

# Task 7 – Train the Linear Learner Model

## Why Linear Learner?

Linear Learner is optimized for:

* Large-scale datasets
* Fast training
* High-dimensional sparse features
* Baseline models

Configure the estimator.

```python
from sagemaker import image_uris

container = image_uris.retrieve(
    "linear-learner",
    region=session.boto_region_name
)

linear = Estimator(
    image_uri=container,
    role=role,
    instance_count=1,
    instance_type="ml.m5.large",
    output_path=output_path,
    sagemaker_session=session
)
```

Hyperparameters

```python
linear.set_hyperparameters(
    predictor_type="binary_classifier",
    mini_batch_size=100,
    epochs=15
)
```

Launch training.

```python
linear.fit({
    "train": TrainingInput(train_path)
})
```

---

# Task 8 – Train a Random Forest Model

## Why Scikit-Learn?

Scikit-Learn allows custom Python scripts while still using managed SageMaker infrastructure.

Create a training script named:

```text
train_rf.py
```

The script should:

* Load the training data.
* Split features and labels.
* Train a `RandomForestClassifier`.
* Save the model using `joblib`.

Configure the Scikit-Learn estimator.

```python
from sagemaker.sklearn.estimator import SKLearn

rf = SKLearn(
    entry_point="train_rf.py",
    role=role,
    instance_type="ml.m5.large",
    framework_version="1.2-1",
    output_path=output_path
)
```

Launch the training job.

```python
rf.fit({"train": train_path})
```

---

# Task 9 – (Optional) Train LightGBM

Advanced Exercise

Participants build a custom Docker image containing:

* Python
* LightGBM
* Training script

Push the image to Amazon ECR and configure a SageMaker Estimator using the custom container.

Discussion:

* When is a Bring Your Own Container (BYOC) approach required?
* What are the operational trade-offs?

---

# Task 10 – Compare Training Jobs

Review all training jobs in the SageMaker console.

Compare:

* Training duration
* Instance type
* Resource consumption
* Model artifact size
* Training logs

Discussion:

* Which model trained the fastest?
* Which consumed the most compute?

---

# Task 11 – Review Model Artifacts

Navigate to the `models/` folder in Amazon S3.

Expected structure:

```text
models/

xgboost/

model.tar.gz

linear-learner/

model.tar.gz

random-forest/

model.tar.gz
```

Discuss:

* What does `model.tar.gz` contain?
* Why are artifacts compressed?

---

# Task 12 – Review CloudWatch Logs

Navigate to:

```text
CloudWatch

↓

Logs

↓

SageMaker
```

Observe:

* Training progress
* Loss values
* Errors
* Warnings

Discussion:

* How do CloudWatch logs assist in troubleshooting?

---

# Task 13 – Validate Training Success

Verify that:

* All training jobs completed successfully.
* Model artifacts exist in Amazon S3.
* No training errors occurred.
* Training logs are available.

---

# Deliverables for Phase 4

Participants should submit:

1. **Training notebook** with all estimator configurations.
2. **Training scripts** (e.g., `train_rf.py`).
3. **Model artifacts** stored in Amazon S3.
4. **Screenshots** of SageMaker Training Jobs.
5. **CloudWatch log excerpts** showing successful execution.
6. **Comparison table** summarizing training duration, instance type, and model artifact locations.

---

# Discussion Questions

Conclude the phase by discussing:

1. Why use SageMaker Training Jobs instead of training directly in a notebook?
2. What are the strengths and weaknesses of XGBoost, Linear Learner, and Random Forest for churn prediction?
3. How do instance type and instance count affect training performance and cost?
4. When would you choose a custom container over a built-in SageMaker algorithm?
5. Why is it important to separate model artifacts from notebooks and source code?

---

# Transition to Phase 5

At the end of this phase, participants have multiple trained models but have not yet optimized them. In **Phase 5 – Hyperparameter Tuning and Experiment Tracking**, they will:

* Optimize model hyperparameters using **SageMaker Hyperparameter Tuning Jobs**.
* Track training runs and metadata using **SageMaker Experiments**.
* Identify the best-performing model based on objective metrics before proceeding to evaluation and deployment.

This reflects the enterprise practice of iteratively improving models before promoting them toward production.
