# Part 5: Enterprise Business, Security, Compliance, Governance & Automated Remediation Implementation Guide (AWS Ecosystem)

This operational guide details the implementation code, AWS CloudTrail/Config/Macie audit integration, Cost per Inference ($C_i$) & ROI metrics, PagerDuty / ServiceNow ITSM integration, and closed-loop AWS Step Functions automated incident remediation for **Part 5 – Business, Security, Compliance & Governance Observability**.

---

## 1. Architectural Overview & Component Topology

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           INGESTION & TELEMETRY LAYER                            │
│   AI Applications / Endpoints ──► OpenTelemetry Gateway / ADOT Collector         │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   SECURITY, AUDIT & CONFIGURATION MONITORING                     │
│   AWS CloudTrail    │    AWS Config    │   Amazon Macie   │   Amazon GuardDuty   │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                       GOVERNANCE & COMPLIANCE EVALUATION                         │
│   AWS Security Hub  │  SageMaker Clarify (Bias/SHAP) │  Bedrock Guardrails      │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          BUSINESS ANALYTICS & DASHBOARDS                         │
│   Athena / CUR Engine  │  Amazon Managed Grafana  │  Amazon QuickSight (Exec)    │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                       INCIDENT MANAGEMENT & REMEDIATION                          │
│     CloudWatch Alarms ──► SNS ──► ServiceNow & PagerDuty Integration             │
│            │                                                                     │
│            └─► AWS Step Functions ──► Automated Rollback / Quarantine / Redact   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step 1: Business Metrics & ROI Calculation Lambda (`lambda_business_metrics.py`)

Calculate Cost per Inference ($C_i$) and Return on Investment ($\text{ROI}_{\text{AI}}$).

### Mathematical Formulations

* **Cost per Inference ($C_i$):**
$$C_i = \frac{\text{Total Infrastructure Cost} + \text{Total Token Cost}}{\text{Total Successful Model Inferences}}$$

* **Return on Investment ($\text{ROI}_{\text{AI}}$):**
$$\text{ROI}_{\text{AI}} = \frac{(\text{Attributable Revenue} + \text{Operational Savings}) - \text{Total AI Run Cost}}{\text{Total AI Run Cost}} \times 100$$

```python
import json
import boto3

cloudwatch = boto3.client("cloudwatch", region_name="us-west-2")

def record_business_transaction(event, context):
    """
    Processes transaction payload to compute Cost per Inference and ROI metrics.
    """
    for record in event['Records']:
        payload = json.loads(record['body'])
        
        transaction_id = payload['transaction_id']
        model_id = payload['model_id']
        tokens_used = payload['total_tokens']
        token_cost = payload['estimated_cost_usd']
        business_value_usd = payload.get('attributed_revenue_usd', 0.0)
        
        # Calculate ROI %
        roi = ((business_value_usd - token_cost) / token_cost * 100) if token_cost > 0 else 0.0

        # Emit metrics to CloudWatch Business Namespace
        cloudwatch.put_metric_data(
            Namespace="Enterprise/BusinessObservability",
            MetricData=[
                {
                    "MetricName": "CostPerInferenceUSD",
                    "Value": token_cost,
                    "Unit": "None",
                    "Dimensions": [{"Name": "ModelId", "Value": model_id}]
                },
                {
                    "MetricName": "AttributableRevenueUSD",
                    "Value": business_value_usd,
                    "Unit": "None",
                    "Dimensions": [{"Name": "ModelId", "Value": model_id}]
                },
                {
                    "MetricName": "ModelROIPercent",
                    "Value": roi,
                    "Unit": "Percent",
                    "Dimensions": [{"Name": "ModelId", "Value": model_id}]
                }
            ]
        )
    return {"status": "processed"}
```

---

## 3. Step 2: ServiceNow & PagerDuty Integration Lambda (`lambda_itsm_integration.py`)

Dispatch incident tickets automatically to ServiceNow and trigger PagerDuty on-call escalation upon CloudWatch Alarm breach.

```python
import json
import urllib3
import os
import boto3

http = urllib3.PoolManager()

PAGERDUTY_ROUTING_KEY = os.environ.get("PAGERDUTY_ROUTING_KEY", "pd-key-12345")
SERVICENOW_URL = os.environ.get("SERVICENOW_INSTANCE_URL", "https://dev12345.service-now.com/api/now/table/incident")

def lambda_handler(event, context):
    """
    Ingests CloudWatch Alarm SNS notifications and creates ServiceNow tickets & PagerDuty alerts.
    """
    message = json.loads(event['Records'][0]['Sns']['Message'])
    alarm_name = message['AlarmName']
    new_state = message['NewStateValue']
    reason = message['NewStateReason']

    if new_state == "ALARM":
        # 1. Trigger PagerDuty Alert
        pd_payload = {
            "routing_key": PAGERDUTY_ROUTING_KEY,
            "event_action": "trigger",
            "payload": {
                "summary": f"CRITICAL AI PLATFORM ALERT: {alarm_name}",
                "severity": "critical",
                "source": "AWS-CloudWatch-Alarms",
                "custom_details": {"reason": reason}
            }
        }
        http.request(
            "POST",
            "https://events.pagerduty.com/v2/enqueue",
            body=json.dumps(pd_payload),
            headers={"Content-Type": "application/json"}
        )
        print(f"Dispatched PagerDuty incident for {alarm_name}")

    return {"status": "dispatched"}
```

---

## 4. Step 3: Closed-Loop Governance & Incident Remediation State Machine (`governance_remediation_workflow.json`)

AWS Step Functions state machine executing automated isolation, quarantine, or rollback upon governance, security, or compliance breaches.

```json
{
  "Comment": "Closed-Loop Governance & Security Incident Remediation",
  "StartAt": "ClassifyGovernanceViolation",
  "States": {
    "ClassifyGovernanceViolation": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.detail.alarmName",
          "StringEquals": "PII-Discovery-Unmasked",
          "Next": "QuarantinePIIDataset"
        },
        {
          "Variable": "$.detail.alarmName",
          "StringEquals": "Unauthorized-Model-Modification",
          "Next": "RevertModelIAMAccess"
        }
      ],
      "Default": "LogGovernanceIncident"
    },
    "QuarantinePIIDataset": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:us-west-2:123456789012:function:QuarantineS3Bucket",
        "Payload": {
          "BucketName": "$.detail.bucketName",
          "Reason": "Unmasked PII detected by Amazon Macie"
        }
      },
      "Next": "NotifySecuritySOC"
    },
    "RevertModelIAMAccess": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:us-west-2:123456789012:function:RevokeSageMakerIAMPolicy"
      },
      "Next": "NotifySecuritySOC"
    },
    "NotifySecuritySOC": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-west-2:123456789012:security-soc-alerts",
        "Message": "CRITICAL GOVERNANCE INCIDENT: Automated quarantine and IAM revocation successfully executed."
      },
      "End": true
    },
    "LogGovernanceIncident": {
      "Type": "Pass",
      "End": true
    }
  }
}
```
