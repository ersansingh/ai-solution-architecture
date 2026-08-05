# Part 4: Enterprise Generative AI & LLM Observability Engineering Implementation Guide (AWS Ecosystem)

This operational guide details the implementation code, ADOT OTel GenAI instrumentation, Judge LLM RAG evaluators (Groundedness, Recall, Precision), Amazon Bedrock Guardrails Terraform IaC, Prompt Injection detection, Token cost accounting, and automated fallback routing workflows for **Part 4 – Generative AI & LLM Observability**.

---

## 1. Architectural Overview & Component Topology

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                INGESTION & INSTRUMENTATION                                │
│   User Request ──► API Gateway / ALB ──► Bedrock / SageMaker ──► ADOT Instrumentation     │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                               PAYLOAD CAPTURE & VECTOR SEARCH                             │
│   Prompt & Completion Store (S3)  │  OpenSearch Serverless (Vector Store)  │  PII Masking  │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                             EVALUATION & SAFETY ENGINE                                    │
│   RAG Metrics (Lambda/Processing)  │  Amazon Bedrock Guardrails  │  SageMaker Clarify      │
│   (Groundedness, Recall, Precision)    (Toxicity, Injection, Bias)   (Semantic Drift, SHAP) │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                          TELEMETRY & CLOSED-LOOP REMEDIATION                              │
│   CloudWatch Alarms ──► Step Functions ──► Fallback Model Routing / Cost Enforcement      │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step 1: OpenTelemetry GenAI Instrumentation (`genai_instrumentation.py`)

Instrument application LLM calls with OpenTelemetry semantic conventions for TTFT, TPOT, input/output tokens, and payload capture.

```python
import json
import time
import boto3
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("genai.observability.tracer")
meter = metrics.get_meter("genai.observability.meter")

token_counter = meter.create_counter(
    "genai.tokens.usage",
    unit="1",
    description="Measures input and output token usage"
)
latency_histogram = meter.create_histogram(
    "genai.latency.ttft",
    unit="ms",
    description="Time To First Token / First Chunk Latency"
)

bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")
s3 = boto3.client("s3")

def invoke_llm_with_observability(prompt, session_id, model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"):
    with tracer.start_as_current_span("bedrock.invoke_model") as span:
        span.set_attribute("genai.system", "aws.bedrock")
        span.set_attribute("genai.request.model", model_id)
        span.set_attribute("genai.session_id", session_id)
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        })
        
        start_time = time.time()
        response = bedrock.invoke_model(modelId=model_id, body=body)
        latency = (time.time() - start_time) * 1000
        
        response_body = json.loads(response.get("body").read())
        completion_text = response_body['content'][0]['text']
        
        input_tokens = response_body['usage']['input_tokens']
        output_tokens = response_body['usage']['output_tokens']
        
        # Record Telemetry Metrics
        token_counter.add(input_tokens, {"token_type": "input", "model": model_id})
        token_counter.add(output_tokens, {"token_type": "output", "model": model_id})
        latency_histogram.record(latency, {"model": model_id})
        
        span.set_attribute("genai.usage.input_tokens", input_tokens)
        span.set_attribute("genai.usage.output_tokens", output_tokens)
        span.set_status(Status(StatusCode.OK))
        
        # Persist Payload (S3) for Async Evaluation Pipeline
        save_payload_to_s3(session_id, prompt, completion_text, input_tokens, output_tokens)
        
        return completion_text

def save_payload_to_s3(session_id, prompt, completion, input_tok, output_tok):
    payload = {
        "session_id": session_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prompt": prompt,
        "completion": completion,
        "tokens": {"input": input_tok, "output": output_tok}
    }
    s3.put_object(
        Bucket="prod-genai-observability-payloads",
        Key=f"raw-logs/{session_id}-{int(time.time())}.json",
        Body=json.dumps(payload)
    )
```

---

## 3. Step 2: Judge LLM RAG Groundedness Evaluator (`lambda_rag_evaluator.py`)

Evaluate RAG Groundedness score (verifying that claims in completion are supported by retrieved context).

### Mathematical Formulation
$$\text{Groundedness} = \frac{\vert{}\text{Claims in Response Supported by Context}\vert{}}{\vert{}\text{Total Distinct Claims in Response}\vert{}}$$

```python
import json
import boto3

bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")
cw = boto3.client("cloudwatch", region_name="us-west-2")

def evaluate_groundedness(response_text, retrieved_contexts):
    """
    Evaluates response groundedness against retrieved context using a Judge LLM (Claude Haiku).
    """
    context_str = "\n---\n".join(retrieved_contexts)
    eval_prompt = f"""You are an expert evaluator. Analyze the Response against the Context.
Determine if every claim made in the Response is directly supported by the Context.
Provide a numerical score between 0.0 (Hallucinated/Unsupported) and 1.0 (Fully Grounded).

Context:
{context_str}

Response:
{response_text}

Output JSON format: {{"groundedness_score": <float>}}
"""
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": eval_prompt}]
    })
    
    res = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0", 
        body=body
    )
    res_json = json.loads(res['body'].read()['content'][0]['text'])
    groundedness = float(res_json['groundedness_score'])

    # Emit Groundedness Metric to CloudWatch
    cw.put_metric_data(
        Namespace="Enterprise/GenAIRAG",
        MetricData=[{
            "MetricName": "GroundednessScore",
            "Value": groundedness,
            "Unit": "None"
        }]
    )
    return groundedness
```

---

## 4. Step 3: Amazon Bedrock Guardrails Deployment (Terraform)

Deploy Amazon Bedrock Guardrail configuration enforcing filters for toxicity, PII masking, and contextual grounding.

```hcl
resource "aws_bedrock_guardrail" "genai_safety_guardrail" {
  name        = "enterprise-genai-guardrail"
  description = "Filters prompt injections, jailbreaks, PII, and toxic outputs"

  content_policy_config {
    filters_config {
      type           = "HATE"
      input_strength = "HIGH"
      output_strength= "HIGH"
    }
    filters_config {
      type           = "VIOLENCE"
      input_strength = "HIGH"
      output_strength= "HIGH"
    }
  }

  sensitive_information_policy_config {
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "BLOCK"
    }
  }

  contextual_grounding_policy_config {
    filters_config {
      type      = "GROUNDING"
      threshold = 0.85
    }
    filters_config {
      type      = "RELEVANCE"
      threshold = 0.80
    }
  }
}
```

---

## 5. Step 4: Token Cost Calculation & Token Budget Monitor (`calculate_genai_cost.py`)

Calculate USD spend based on input and output token volume and model pricing tiers.

```python
import boto3

cw = boto3.client("cloudwatch", region_name="us-west-2")

PRICING_TABLE = {
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 0.003 / 1000, "output": 0.015 / 1000},
    "anthropic.claude-3-haiku-20240307-v1:0": {"input": 0.00025 / 1000, "output": 0.00125 / 1000},
    "amazon.nova-micro-v1:0": {"input": 0.000035 / 1000, "output": 0.00014 / 1000}
}

def compute_conversation_cost(model_id, input_tokens, output_tokens):
    if model_id not in PRICING_TABLE:
        return 0.0
    
    rates = PRICING_TABLE[model_id]
    cost = (input_tokens * rates["input"]) + (output_tokens * rates["output"])
    
    # Push to CloudWatch Cost Metrics
    cw.put_metric_data(
        Namespace="Enterprise/GenAICost",
        MetricData=[{
            "MetricName": "EstimatedTokenCostUSD",
            "Value": cost,
            "Unit": "None",
            "Dimensions": [{"Name": "ModelId", "Value": model_id}]
        }]
    )
    return cost
```

---

## 6. Step 5: Automated Fallback & Cost Control State Machine (`genai_remediation_workflow.json`)

AWS Step Functions workflow executing automated fallback routing when groundedness fails or budget is exceeded.

```json
{
  "Comment": "Automated Remediation Workflow for GenAI System Violations",
  "StartAt": "EvaluateIncidentType",
  "States": {
    "EvaluateIncidentType": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.detail.alarmName",
          "StringEquals": "GenAI-Low-Groundedness-Alert",
          "Next": "SwitchToFallbackModel"
        },
        {
          "Variable": "$.detail.alarmName",
          "StringEquals": "GenAI-Budget-Exceeded",
          "Next": "EnforceModelCostRouting"
        }
      ],
      "Default": "DefaultAlert"
    },
    "SwitchToFallbackModel": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:us-west-2:123456789012:function:UpdateModelRoutingParameter",
        "Payload": {
          "RoutingMode": "STRICT_GROUNDING",
          "ModelId": "anthropic.claude-3-haiku-20240307-v1:0"
        }
      },
      "Next": "NotifyTeamOfModelSwitch"
    },
    "EnforceModelCostRouting": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:us-west-2:123456789012:function:UpdateModelRoutingParameter",
        "Payload": {
          "RoutingMode": "COST_OPTIMIZED",
          "ModelId": "amazon.nova-micro-v1:0"
        }
      },
      "Next": "NotifyFinanceSlack"
    },
    "NotifyTeamOfModelSwitch": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-west-2:123456789012:genai-alerts-topic",
        "Message": "AUTOMATED REMEDIATION: Model routing switched to Claude Haiku due to low groundedness."
      },
      "End": true
    },
    "NotifyFinanceSlack": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-west-2:123456789012:slack-finance-topic",
        "Message": "COST CONTROL: Budget limit reached. Prompts automatically rerouted to Amazon Nova Micro."
      },
      "End": true
    },
    "DefaultAlert": {
      "Type": "Pass",
      "End": true
    }
  }
}
```
