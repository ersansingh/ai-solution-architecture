# Phase 3 – Data Preparation and Feature Engineering

## Lab Guide: Preparing Production-Ready Data for Machine Learning

**Lab Duration:** 2–2.5 Hours

---

# Phase Objective

In this phase, participants will transform the raw, integrated dataset produced during Phase 2 into a machine learning-ready dataset. This includes cleaning the data, handling missing values, encoding categorical variables, scaling numerical features, engineering new business features, validating data quality, and storing engineered features in **Amazon SageMaker Feature Store**.

This phase reflects the responsibilities of an ML Engineer or AI Solutions Architect preparing high-quality features for model training.

---

# Learning Objectives

By the end of this phase, participants will be able to:

* Assess and improve data quality.
* Handle missing values and outliers appropriately.
* Encode categorical variables for machine learning algorithms.
* Normalize or standardize numerical features.
* Engineer domain-specific features that improve predictive performance.
* Store features in Amazon SageMaker Feature Store.
* Split the data into training, validation, and test sets.
* Save processed datasets back to Amazon S3.

---

# Phase Architecture

```text
Amazon S3 (Integrated Dataset)
            │
            ▼
SageMaker Processing / Notebook
            │
            ▼
Data Cleaning
            │
            ▼
Feature Engineering
            │
            ▼
Feature Validation
            │
            ├──────────────► Amazon SageMaker Feature Store
            │
            ▼
Train / Validation / Test Split
            │
            ▼
Amazon S3 (Training Data)
```

---

# Input Dataset

From Phase 2:

```text
s3://teleconnect-churn-lab/processed-data/customer_churn_master.csv
```

---

# Expected Output

```text
processed-data/

customer_churn_clean.csv

training/

train.csv

validation.csv

test.csv

feature-store/

customer_features.csv
```

---

# Task 1 – Load the Integrated Dataset

## Objective

Read the master dataset created in Phase 2.

```python
import pandas as pd

df = pd.read_csv(
    f"s3://{bucket}/processed-data/customer_churn_master.csv"
)

df.head()
```

---

Expected Result

Integrated dataset loaded successfully.

---

# Task 2 – Review Data Quality

## Objective

Identify issues before cleaning.

Run

```python
df.info()

df.describe(include="all")

df.isnull().sum()

df.duplicated().sum()
```

---

Discussion

Ask participants:

* Which columns contain missing values?
* Which columns are categorical?
* Which columns are numerical?
* Which features appear problematic?

---

Deliverable

Data quality assessment.

---

# Task 3 – Handle Missing Values

## Objective

Prepare a complete dataset for training.

### Numerical Columns

Examples

```text
monthly_charges

total_charges

data_usage_gb

voice_minutes

satisfaction_score
```

Fill using median:

```python
num_cols = [
    "monthly_charges",
    "total_charges",
    "data_usage_gb",
    "voice_minutes",
    "satisfaction_score"
]

for col in num_cols:
    df[col].fillna(df[col].median(), inplace=True)
```

---

### Categorical Columns

Examples

```text
payment_method

region

contract_type

customer_segment
```

Fill using most frequent value:

```python
cat_cols = [
    "payment_method",
    "region",
    "contract_type",
    "customer_segment"
]

for col in cat_cols:
    df[col].fillna(df[col].mode()[0], inplace=True)
```

---

Expected Result

No missing values remain.

Verify

```python
df.isnull().sum()
```

---

# Task 4 – Remove Duplicate Records

```python
df = df.drop_duplicates()
```

Verify

```python
df.duplicated().sum()
```

Expected

```text
0
```

---

# Task 5 – Outlier Detection

## Objective

Identify extreme values.

Use IQR.

Example

```python
Q1 = df["monthly_charges"].quantile(0.25)

Q3 = df["monthly_charges"].quantile(0.75)

IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR

upper = Q3 + 1.5 * IQR
```

Identify

```python
outliers = df[
    (df["monthly_charges"] < lower) |
    (df["monthly_charges"] > upper)
]
```

Discussion

Should outliers

* remain?
* be capped?
* be removed?

---

Recommended

Cap instead of deleting.

---

# Task 6 – Encode Target Variable

Convert

```text
Yes → 1

No → 0
```

```python
df["churn"] = df["churn"].map({
    "Yes":1,
    "No":0
})
```

---

Expected Result

Binary target variable.

---

# Task 7 – Encode Categorical Features

## Objective

Convert text into numeric values.

Columns

```text
gender

region

payment_method

contract_type

internet_package

customer_segment

streaming_service
```

Use One-Hot Encoding.

```python
df = pd.get_dummies(
    df,
    columns=[
        "gender",
        "region",
        "payment_method",
        "contract_type",
        "internet_package",
        "customer_segment",
        "streaming_service"
    ],
    drop_first=True
)
```

Discussion

Why use One-Hot Encoding?

* Avoid ordinal relationships.
* Compatible with tree-based algorithms.
* Required by many ML algorithms.

---

# Task 8 – Scale Numerical Features

## Objective

Normalize features for algorithms such as Linear Learner.

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()

numeric_cols = [
    "monthly_charges",
    "total_charges",
    "voice_minutes",
    "data_usage_gb",
    "roaming_minutes",
    "tenure_months",
    "tickets",
    "avg_resolution_hours",
    "outstanding_balance"
]

df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
```

Discussion

Which algorithms require scaling?

* Linear Learner
* Logistic Regression
* Neural Networks
* KNN
* SVM

Tree-based algorithms (e.g., XGBoost, Random Forest) are generally less sensitive to scaling.

---

# Task 9 – Feature Engineering

## Objective

Create new business features.

### Feature 1 – Customer Lifetime Value

```python
df["customer_lifetime_value"] = (
    df["monthly_charges"] *
    df["tenure_months"]
)
```

Business Meaning

Estimated revenue generated.

---

### Feature 2 – Average Monthly Spend

```python
df["average_monthly_spend"] = (
    df["total_charges"] /
    (df["tenure_months"] + 1)
)
```

---

### Feature 3 – Complaint Ratio

```python
df["complaint_ratio"] = (
    df["complaint_count"] /
    (df["tickets"] + 1)
)
```

---

### Feature 4 – Support Calls per Month

```python
df["support_calls_per_month"] = (
    df["support_calls"] /
    (df["tenure_months"] + 1)
)
```

---

### Feature 5 – Payment Risk

```python
df["payment_risk"] = (
    df["outstanding_balance"] /
    (df["monthly_charges"] + 1)
)
```

---

### Feature 6 – Customer Engagement Score

Example formula

```python
df["engagement_score"] = (
    df["voice_minutes"] +
    df["data_usage_gb"] -
    df["complaint_count"] * 10
)
```

---

### Feature 7 – Customer Risk Score

```python
df["risk_score"] = (
    df["complaint_count"]*2 +
    df["support_calls"] +
    (10-df["satisfaction_score"])
)
```

---

Discussion

Ask participants:

* Which engineered features are likely to improve churn prediction?
* Which are business-friendly and explainable?

---

# Task 10 – Validate Engineered Features

Run

```python
df.describe()
```

Check

* Missing values
* Negative values
* Unexpected distributions

---

# Task 11 – Store Features in SageMaker Feature Store

## Objective

Persist reusable features for future model training.

Example workflow

```text
Feature Engineering
        │
        ▼
Feature Group
        │
        ▼
Offline Store (Amazon S3)
        │
        ▼
Online Store (Optional)
```

Feature Group Example

```text
CustomerFeatureGroup
```

Store

* customer_id
* engineered features
* event_time

Discussion

Explain:

* Offline Store for batch training.
* Online Store for low-latency inference.
* Feature reuse across multiple ML models.

---

# Task 12 – Split Dataset

## Objective

Create training, validation, and test datasets.

Recommended

```text
70% Training

15% Validation

15% Test
```

Example

```python
from sklearn.model_selection import train_test_split

train, temp = train_test_split(
    df,
    test_size=0.30,
    random_state=42,
    stratify=df["churn"]
)

validation, test = train_test_split(
    temp,
    test_size=0.50,
    random_state=42,
    stratify=temp["churn"]
)
```

Discussion

Why stratified sampling?

* Preserves class distribution across splits.
* Produces more reliable evaluation.

---

# Task 13 – Save Datasets Locally

```python
train.to_csv("train.csv", index=False)

validation.to_csv("validation.csv", index=False)

test.to_csv("test.csv", index=False)

df.to_csv("customer_churn_clean.csv", index=False)
```

---

# Task 14 – Upload to Amazon S3

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

session.upload_data(
    "test.csv",
    bucket=bucket,
    key_prefix="training"
)

session.upload_data(
    "customer_churn_clean.csv",
    bucket=bucket,
    key_prefix="processed-data"
)
```

Expected Structure

```text
processed-data/

customer_churn_clean.csv

training/

train.csv

validation.csv

test.csv
```

---

# Task 15 – Validate Training Files

Verify

* Number of records in each split.
* Similar churn distribution across train, validation, and test sets.
* No missing values.
* Target column present.
* Feature columns consistent.

---

# Deliverables for Phase 3

Participants should produce:

1. Cleaned customer dataset.
2. Feature engineering notebook.
3. Document describing engineered features and business rationale.
4. Training, validation, and test datasets uploaded to Amazon S3.
5. SageMaker Feature Store populated with engineered features.
6. Data quality validation report.

---

# Discussion Questions

Conclude the phase by discussing:

1. Which engineered features are expected to contribute most to churn prediction?
2. Why is One-Hot Encoding preferred over Label Encoding for nominal categories?
3. Why is feature scaling important for some algorithms but not others?
4. What are the benefits of storing reusable features in SageMaker Feature Store?
5. How do train, validation, and test datasets support unbiased model evaluation?

By the end of Phase 3, participants will have a production-ready feature dataset and standardized data pipeline, establishing the foundation for **Phase 4**, where multiple machine learning models will be trained and compared using Amazon SageMaker Training Jobs, SageMaker Experiments, and Hyperparameter Tuning.
