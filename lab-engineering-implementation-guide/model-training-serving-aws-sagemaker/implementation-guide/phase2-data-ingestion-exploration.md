# Phase 2 – Data Ingestion and Data Exploration (EDA)

## Lab Guide: Uploading Data and Understanding the Customer Churn Dataset

**Lab Duration:** 90–120 Minutes

---

# Phase Objective

After completing this phase, participants will be able to:

* Understand the business dataset.
* Upload enterprise datasets into Amazon S3.
* Access data from SageMaker Studio.
* Perform exploratory data analysis (EDA).
* Assess data quality.
* Identify missing values, duplicates, outliers, and class imbalance.
* Generate insights that guide feature engineering and model selection.

This phase mirrors the work typically carried out by a Data Scientist or ML Engineer before model development.

---

# Learning Objectives

Participants will learn how to:

* Organize data within an enterprise data lake.
* Load multiple datasets from Amazon S3.
* Join related datasets.
* Explore data distributions.
* Detect data quality issues.
* Produce an EDA report suitable for stakeholders.
* Decide on preprocessing strategies based on observed patterns.

---

# Dataset Overview

The telecommunications company provides data from multiple operational systems.

```text
CRM System
      │
      ▼
customers.csv

Billing System
      │
      ▼
billing.csv

Network System
      │
      ▼
usage.csv

Support System
      │
      ▼
support.csv

Analytics Team
      │
      ▼
churn.csv
```

Each file contains information for the same set of customers and can be joined using the **customer_id** column.

---

# Dataset Details

## customers.csv

| Column           | Description                    |
| ---------------- | ------------------------------ |
| customer_id      | Unique customer identifier     |
| age              | Customer age                   |
| gender           | Male/Female                    |
| region           | Customer location              |
| customer_segment | Consumer, Business, Enterprise |
| tenure_months    | Customer tenure                |

---

## billing.csv

| Column              | Description          |
| ------------------- | -------------------- |
| monthly_charges     | Monthly subscription |
| total_charges       | Lifetime billing     |
| payment_method      | Payment mode         |
| outstanding_balance | Pending amount       |
| contract_type       | Contract duration    |

---

## usage.csv

| Column            | Description            |
| ----------------- | ---------------------- |
| internet_package  | Internet plan          |
| voice_minutes     | Monthly voice usage    |
| data_usage_gb     | Monthly data usage     |
| roaming_minutes   | Roaming usage          |
| support_calls     | Number of calls        |
| streaming_service | Streaming subscription |

---

## support.csv

| Column               | Description     |
| -------------------- | --------------- |
| tickets              | Support tickets |
| avg_resolution_hours | Resolution time |
| complaint_count      | Complaints      |
| satisfaction_score   | Customer rating |

---

## churn.csv

| Column | Description     |
| ------ | --------------- |
| churn  | Target Variable |

---

# Architecture

```text
CSV Files
      │
      ▼
Amazon S3
      │
      ▼
SageMaker Studio
      │
      ▼
Pandas DataFrames
      │
      ▼
Data Validation
      │
      ▼
EDA
      │
      ▼
EDA Report
```

---

# Task 1 – Upload Dataset to Amazon S3

## Objective

Store raw datasets in the data lake.

### Folder Structure

```
raw-data/

    customers.csv
    billing.csv
    usage.csv
    support.csv
    churn.csv
```

---

### Steps

Navigate to

Amazon S3

↓

Your Bucket

↓

raw-data/

↓

Upload

Select

* customers.csv
* billing.csv
* usage.csv
* support.csv
* churn.csv

---

Expected Result

```
raw-data/

customers.csv

billing.csv

usage.csv

support.csv

churn.csv
```

---

# Task 2 – Create an EDA Notebook

Create a new notebook:

```
02_Data_Exploration.ipynb
```

---

# Task 3 – Import Required Libraries

```python
import boto3
import sagemaker
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
```

---

# Task 4 – Configure AWS Session

```python
session = sagemaker.Session()

bucket = "teleconnect-churn-yourname-lab"

prefix = "raw-data"
```

---

# Task 5 – Read Data from Amazon S3

```python
customers = pd.read_csv(f"s3://{bucket}/raw-data/customers.csv")

billing = pd.read_csv(f"s3://{bucket}/raw-data/billing.csv")

usage = pd.read_csv(f"s3://{bucket}/raw-data/usage.csv")

support = pd.read_csv(f"s3://{bucket}/raw-data/support.csv")

churn = pd.read_csv(f"s3://{bucket}/raw-data/churn.csv")
```

---

# Task 6 – Inspect Each Dataset

For every dataset, inspect:

```python
customers.head()

customers.info()

customers.describe(include="all")

customers.shape
```

Repeat for the remaining datasets.

---

# Discussion

Participants should answer:

* How many rows?
* How many columns?
* Which columns are categorical?
* Which columns are numerical?
* Any unexpected values?

---

# Task 7 – Validate Primary Keys

Verify uniqueness of **customer_id**.

```python
customers["customer_id"].is_unique
```

Expected Result

```
True
```

Repeat for every table.

---

# Task 8 – Merge the Datasets

Join all datasets using **customer_id**.

```python
df = (
    customers
    .merge(billing,on="customer_id")
    .merge(usage,on="customer_id")
    .merge(support,on="customer_id")
    .merge(churn,on="customer_id")
)
```

---

Verify

```python
df.shape
```

---

Expected Result

A single integrated dataset ready for analysis.

---

# Task 9 – Examine Overall Structure

```python
df.info()
```

Identify:

* Numerical columns
* Categorical columns
* Target variable

---

# Task 10 – Check Missing Values

```python
df.isnull().sum()
```

Questions

* Which columns have missing values?
* Are missing values random?
* Should they be removed or imputed?

---

# Task 11 – Detect Duplicate Records

```python
df.duplicated().sum()
```

If duplicates exist

```python
df.drop_duplicates(inplace=True)
```

---

# Task 12 – Explore Target Variable

```python
df["churn"].value_counts()
```

Create a bar chart.

```python
df["churn"].value_counts().plot(kind="bar")
plt.show()
```

---

Discussion

* Is the dataset balanced?
* Would imbalance affect model training?
* Should class weights or resampling be considered?

---

# Task 13 – Summary Statistics

Generate descriptive statistics.

```python
df.describe()
```

Analyze:

* Mean
* Standard deviation
* Minimum
* Maximum
* Quartiles

---

# Task 14 – Distribution Analysis

Plot histograms for numerical columns.

```python
df.hist(figsize=(18,15))
plt.show()
```

Discuss:

* Are variables normally distributed?
* Which are skewed?
* Which may require scaling?

---

# Task 15 – Categorical Analysis

Inspect category frequencies.

```python
df["contract_type"].value_counts()

df["payment_method"].value_counts()

df["region"].value_counts()
```

Discuss:

* Rare categories?
* Dominant categories?
* Need for grouping?

---

# Task 16 – Correlation Analysis

Select numerical columns and compute correlations.

```python
corr = df.select_dtypes(include=["number"]).corr()

corr
```

Visualize using a heatmap (optional).

Questions

* Which variables are strongly correlated?
* Could multicollinearity affect certain models?

---

# Task 17 – Outlier Detection

Use box plots.

```python
numeric_cols = df.select_dtypes(include=["number"]).columns

for col in numeric_cols:
    df.boxplot(column=col)
    plt.title(col)
    plt.show()
```

Discuss:

* Which columns contain outliers?
* Are they valid business values or data errors?

---

# Task 18 – Business Insight Exploration

Investigate relationships between features and churn.

Examples:

### Churn by Contract Type

```python
pd.crosstab(df["contract_type"], df["churn"])
```

### Churn by Region

```python
pd.crosstab(df["region"], df["churn"])
```

### Churn by Satisfaction Score

```python
df.groupby("satisfaction_score")["churn"].value_counts()
```

### Monthly Charges vs Churn

```python
df.groupby("churn")["monthly_charges"].mean()
```

Discussion:

* Which customer groups churn the most?
* What business hypotheses emerge?

---

# Task 19 – Data Quality Assessment

Create a summary table.

| Check              | Status    | Action                      |
| ------------------ | --------- | --------------------------- |
| Missing values     | Pass/Fail | Impute or remove            |
| Duplicate rows     | Pass/Fail | Remove duplicates           |
| Unique customer_id | Pass/Fail | Investigate if duplicated   |
| Outliers           | Pass/Fail | Review before treatment     |
| Class balance      | Pass/Fail | Plan for imbalance handling |

---

# Task 20 – Save the Integrated Dataset

Persist the merged dataset for the next phase.

```python
df.to_csv("customer_churn_master.csv", index=False)
```

Upload to Amazon S3.

```python
session.upload_data(
    "customer_churn_master.csv",
    bucket=bucket,
    key_prefix="processed-data"
)
```

Expected Result

```
processed-data/

customer_churn_master.csv
```

---

# Deliverables for Phase 2

By the end of this phase, participants should have:

1. Uploaded all raw datasets to Amazon S3.
2. Verified dataset integrity and primary keys.
3. Merged the datasets into a single analytical dataset.
4. Completed exploratory data analysis (EDA).
5. Documented data quality issues and potential preprocessing actions.
6. Generated initial business insights related to churn.
7. Saved the consolidated dataset to the `processed-data/` folder in Amazon S3.

---

# Discussion Questions

Conclude the phase by discussing:

1. Which features appear most related to churn?
2. Are there any data quality issues that must be addressed before training?
3. Which features are likely to require encoding or scaling?
4. How might class imbalance influence evaluation metrics?
5. What additional features could be engineered to improve predictive performance?

These observations provide the foundation for **Phase 3**, where participants will clean the data, perform feature engineering, and prepare training-ready datasets for the SageMaker training pipeline.
