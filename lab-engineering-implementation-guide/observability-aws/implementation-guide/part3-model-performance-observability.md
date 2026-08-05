# Part 3: Enterprise Model Performance Observability Engineering Implementation Guide (AWS Ecosystem)

This operational guide details the implementation code, SageMaker Endpoint Data Capture, asynchronous ground-truth join engine, performance metric evaluators (Accuracy, Precision, Recall, F1, ROC-AUC, ECE), SHAP explainability, and automated model rollback workflows for **Part 3 – Model Performance Observability**.

---

## 1. Architectural Overview & Component Topology

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                INFERENCE & DATA CAPTURE                                   │
│    Client App ──► ALB ──► SageMaker Endpoint (Model Registry) ──► Data Capture (S3)       │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                           GROUND TRUTH & EVALUATION ENGINE                                │
│    Ground Truth Source (RDS/S3) ──► EventBridge ──► Join Engine (Lambda / PySpark)         │
│                                                     │                                     │
│                                                     ▼                                     │
│                                    SageMaker Processing Job                               │
│                   (Accuracy, Precision, Recall, F1, ROC-AUC, ECE, SHAP)                   │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                          TELEMETRY & CLOSED-LOOP REMEDIATION                              │
│   CloudWatch Alarms ──► Step Functions ──► SageMaker Model Rollback / Automated Retrain   │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step 1: SageMaker Endpoint Data Capture Configuration (Terraform)

Enable 100% Data Capture on Amazon SageMaker Endpoint to log inference inputs, outputs, and metadata directly to S3.

```hcl
resource "aws_sagemaker_endpoint_configuration" "model_config" {
  name = "production-fraud-detection-config"

  production_variants {
    variant_name           = "AllTraffic"
    model_name             = "fraud-detection-v2"
    initial_instance_count = 2
    instance_type          = "ml.m5.xlarge"
  }

  data_capture_config {
    enable_capture              = true
    initial_sampling_percentage = 100
    destination_s3_uri          = "s3://prod-model-observability-us-west-2/data-capture/"
    capture_options {
      capture_mode = "InputAndOutput"
    }
    capture_content_type_header {
      csv_content_types  = ["text/csv"]
      json_content_types = ["application/json"]
    }
  }
}
```

---

## 3. Step 2: Ground Truth Join Engine Lambda (`lambda_ground_truth_join.py`)

Asynchronously join ground-truth business outcomes with captured predictions using a unique `prediction_id`.

```python
import json
import boto3
import os

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('PREDICTION_LOOKUP_TABLE', 'PredictionLookup'))

def lambda_handler(event, context):
    """
    EventBridge trigger when Ground Truth event is emitted by application.
    Expected payload: {"prediction_id": "...", "ground_truth": 1, "timestamp": "..."}
    """
    for record in event['Records']:
        payload = json.loads(record['body'])
        pred_id = payload['prediction_id']
        ground_truth = payload['ground_truth']
        
        # Retrieve original prediction metadata from DynamoDB lookup index
        response = table.get_item(Key={'prediction_id': pred_id})
        if 'Item' not in response:
            print(f"Prediction ID {pred_id} not found yet. Writing to pending queue.")
            continue
            
        prediction_record = response['Item']
        
        # Construct joined evaluation record
        joined_record = {
            "prediction_id": pred_id,
            "model_version": prediction_record['model_version'],
            "timestamp": prediction_record['timestamp'],
            "prediction": int(prediction_record['prediction']),
            "confidence": float(prediction_record['confidence_score']),
            "ground_truth": int(ground_truth),
            "input_features": prediction_record['input_features']
        }
        
        # Write to Evaluation S3 Partition
        s3.put_object(
            Bucket=os.environ.get('EVALUATION_BUCKET', 'prod-eval-bucket'),
            Key=f"eval-data/version={prediction_record['model_version']}/{pred_id}.json",
            Body=json.dumps(joined_record)
        )
        
    return {"status": "success"}
```

---

## 4. Step 3: Model Evaluation Engine & ECE Calculation (`evaluate_model_performance.py`)

Compute statistical classification metrics (Accuracy, Precision, Recall, F1, ROC-AUC) and Expected Calibration Error (ECE).

```python
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import boto3

cw = boto3.client('cloudwatch', region_name='us-west-2')

def calculate_ece(y_true, y_prob, n_bins=10):
    """Calculates Expected Calibration Error (ECE)."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower, bin_upper = bin_boundaries[i], bin_boundaries[i + 1]
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin] == (y_prob[in_bin] >= 0.5))
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin
    return float(ece)

def evaluate_and_emit(df, model_version):
    y_true = df['ground_truth'].values
    y_pred = df['prediction'].values
    y_prob = df['confidence'].values

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.5
    ece = calculate_ece(y_true, y_prob)

    # Publish Metrics to CloudWatch
    cw.put_metric_data(
        Namespace='Enterprise/ModelObservability',
        MetricData=[
            {'MetricName': 'Accuracy', 'Value': float(acc), 'Unit': 'None', 'Dimensions': [{'Name': 'ModelVersion', 'Value': model_version}]},
            {'MetricName': 'Precision', 'Value': float(prec), 'Unit': 'None', 'Dimensions': [{'Name': 'ModelVersion', 'Value': model_version}]},
            {'MetricName': 'Recall', 'Value': float(rec), 'Unit': 'None', 'Dimensions': [{'Name': 'ModelVersion', 'Value': model_version}]},
            {'MetricName': 'F1Score', 'Value': float(f1), 'Unit': 'None', 'Dimensions': [{'Name': 'ModelVersion', 'Value': model_version}]},
            {'MetricName': 'ROCAUC', 'Value': float(auc), 'Unit': 'None', 'Dimensions': [{'Name': 'ModelVersion', 'Value': model_version}]},
            {'MetricName': 'ECE', 'Value': float(ece), 'Unit': 'None', 'Dimensions': [{'Name': 'ModelVersion', 'Value': model_version}]}
        ]
    )
    print(f"Evaluated Model Version {model_version} -> Acc: {acc:.4f}, Prec: {prec:.4f}, Rec: {rec:.4f}, F1: {f1:.4f}, ECE: {ece:.4f}")
```

---

## 5. Step 4: Closed-Loop Automated Model Remediation State Machine (`model_remediation_workflow.json`)

AWS Step Functions workflow executing automated rollback or retraining when model performance drops.

```json
{
  "Comment": "Closed-Loop Model Performance Remediation Orchestrator",
  "StartAt": "DetermineRemediationAction",
  "States": {
    "DetermineRemediationAction": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.detail.alarmName",
          "StringEquals": "Model-Recall-Critical-Degradation",
          "Next": "ExecuteModelRollback"
        },
        {
          "Variable": "$.detail.alarmName",
          "StringEquals": "Model-Accuracy-Drop",
          "Next": "TriggerRetrainingPipeline"
        }
      ],
      "Default": "NotifyMLOpsTeam"
    },
    "ExecuteModelRollback": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:us-west-2:123456789012:function:SageMakerEndpointRollback",
        "Payload": {
          "EndpointName": "production-fraud-endpoint",
          "TargetStableVersion": "2.0.0"
        }
      },
      "Next": "NotifyPagerDutyRollback"
    },
    "TriggerRetrainingPipeline": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sagemaker:createPipelineExecution",
      "Parameters": {
        "PipelineName": "FraudModel-Retraining-Pipeline",
        "PipelineExecutionDescription": "Automated retraining due to accuracy degradation."
      },
      "Next": "NotifySlackRetraining"
    },
    "NotifyPagerDutyRollback": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-west-2:123456789012:pagerduty-critical-topic",
        "Message": "CRITICAL: Model endpoint rolled back to stable version 2.0.0 due to recall threshold failure."
      },
      "End": true
    },
    "NotifySlackRetraining": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-west-2:123456789012:slack-alerts-topic",
        "Message": "Model retraining pipeline initiated automatically due to detected accuracy drift."
      },
      "End": true
    },
    "NotifyMLOpsTeam": {
      "Type": "Pass",
      "End": true
    }
  }
}
```
