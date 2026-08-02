# Part 2: Enterprise Data & Feature Observability Engineering Implementation Guide (AWS Ecosystem)

This operational guide details the implementation code, AWS Deequ quality checks, Glue Schema Registry integration, SageMaker Model Monitor Population Stability Index (PSI) drift calculation, and automated quarantine workflows for **Part 2 – Data & Feature Observability**.

---

## 1. Architectural Overview & Component Topology

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                INGESTION & DATA LAKE                                      │
│    S3 Data Lake / Kinesis ──► AWS Glue Data Catalog ──► AWS Glue Schema Registry          │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                          DATA QUALITY & PII DISCOVERY ENGINE                              │
│    AWS Deequ (PySpark) Quality Checks  │  AWS Macie PII Scanner  │  SageMaker Feature Store │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                           FEATURE & CONCEPT DRIFT EVALUATOR                               │
│    SageMaker Model Monitor (PSI / KL-Divergence / KS-Test) ──► Custom Metric Exporter     │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                          INCIDENT REMEDIATION & QUARANTINE                                │
│   CloudWatch Alarms ──► Step Functions ──► Quarantine S3 Bucket / Retraining Pipeline     │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step 1: AWS Deequ Data Quality Check (PySpark)

Implement data quality validation checks using PySpark and AWS Deequ (Completeness, Uniqueness, Compliance, Range checks).

### `deequ_data_quality_job.py`
```python
import sys
from pyspark.sql import SparkSession
from pydeequ.checks import Check, CheckLevel
from pydeequ.verification import VerificationEngine, VerificationResult
from pydeequ.repository import FileSystemMetricsRepository, ResultKey
import boto3

spark = SparkSession.builder \
    .appName("EnterpriseDataQualityChecker") \
    .config("spark.jars.packages", "com.amazon.deequ:deequ:2.0.3-spark-3.3") \
    .getOrCreate()

# Load raw incoming Parquet dataset from S3
input_s3_path = "s3://prod-data-observability-us-west-2/raw-transactions/year=2026/month=08/day=02/"
df = spark.read.parquet(input_s3_path)

# Define Deequ Verification Suite
check = Check(spark, CheckLevel.Error, "Transaction Data Quality Check")

checkResult = VerificationEngine(spark) \
    .onData(df) \
    .addCheck(
        check.hasSize(lambda x: x >= 1000) \
             .isComplete("transaction_id") \
             .isUnique("transaction_id") \
             .isComplete("user_id") \
             .hasMin("amount", lambda x: x >= 0.01) \
             .isContainedIn("currency", ["USD", "EUR", "GBP", "JPY"])
    ) \
    .run()

# Parse and evaluate verification output
result_df = VerificationResult.checkResultsAsDataFrame(spark, checkResult)
result_df.show(truncate=False)

# Push metric status to CloudWatch
cw = boto3.client('cloudwatch', region_name='us-west-2')
failed_checks = result_df.filter(result_df.check_status == "Error").count()

cw.put_metric_data(
    Namespace='Enterprise/DataObservability',
    MetricData=[
        {
            'MetricName': 'DataQualityFailedChecks',
            'Value': float(failed_checks),
            'Unit': 'Count'
        }
    ]
)

if failed_checks > 0:
    print(f"CRITICAL: {failed_checks} data quality rules violated. Quarantine required.")
    sys.exit(1)
```

---

## 3. Step 2: Population Stability Index (PSI) Feature Drift Calculation

Calculate Population Stability Index (PSI) to detect distribution drift between baseline training feature distributions and target serving feature distributions.

### Mathematical Formulation
$$\text{PSI} = \sum_{i=1}^{k} \left( P_i - Q_i \right) \times \ln\left(\frac{P_i}{Q_i}\right)$$

Where $P_i$ is actual serving percentage in bin $i$, and $Q_i$ is expected baseline percentage in bin $i$.

### `calculate_psi_drift.py`
```python
import numpy as np
import pandas as pd
import boto3

cw = boto3.client('cloudwatch', region_name='us-west-2')

def calculate_psi(baseline, target, num_bins=10):
    """
    Calculates Population Stability Index (PSI) between baseline and serving distribution.
    PSI < 0.1: No change
    0.1 <= PSI < 0.25: Moderate shift
    PSI >= 0.25: Severe shift (Triggers retraining)
    """
    baseline = np.asarray(baseline)
    target = np.asarray(target)
    
    # Calculate bin thresholds based on baseline quantiles
    percentiles = np.linspace(0, 100, num_bins + 1)
    bins = np.percentile(baseline, percentiles)
    bins[0] = -np.inf
    bins[-1] = np.inf

    # Bucketize distributions
    baseline_counts = np.histogram(baseline, bins=bins)[0]
    target_counts = np.histogram(target, bins=bins)[0]

    # Convert to proportions with zero-smoothing
    P = np.where(baseline_counts == 0, 0.0001, baseline_counts) / len(baseline)
    Q = np.where(target_counts == 0, 0.0001, target_counts) / len(target)

    # Compute PSI
    psi_value = np.sum((Q - P) * np.log(Q / P))
    return float(psi_value)

# Example usage emitting to CloudWatch
if __name__ == "__main__":
    baseline_data = np.random.normal(loc=50, scale=10, size=10000)
    serving_data = np.random.normal(loc=65, scale=12, size=5000) # Drifted distribution
    
    psi_score = calculate_psi(baseline_data, serving_data)
    print(f"Computed Feature PSI Drift Score: {psi_score:.4f}")

    cw.put_metric_data(
        Namespace='Enterprise/DataObservability',
        MetricData=[
            {
                'MetricName': 'FeatureDriftPSI',
                'Value': psi_score,
                'Unit': 'None',
                'Dimensions': [{'Name': 'FeatureName', 'Value': 'customer_age'}]
            }
        ]
    )
```

---

## 4. Step 3: Terraform CloudWatch Alarm & Remediation Trigger

Deploy a CloudWatch alarm that monitors PSI drift and triggers an AWS Step Functions workflow when PSI $\ge 0.25$.

```hcl
resource "aws_cloudwatch_metric_alarm" "psi_critical_drift" {
  alarm_name          = "DataDrift-PSI-Critical-Threshold"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "FeatureDriftPSI"
  namespace           = "Enterprise/DataObservability"
  period              = 300
  statistic           = "Maximum"
  threshold           = 0.25
  alarm_description   = "Critical PSI feature drift detected (>= 0.25). Triggers SageMaker retraining."

  dimensions = {
    FeatureName = "customer_age"
  }

  alarm_actions = [aws_sns_topic.data_remediation_topic.arn]
}
```
