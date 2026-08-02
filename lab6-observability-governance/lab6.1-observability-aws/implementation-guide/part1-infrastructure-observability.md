# Part 1: Infrastructure Observability Engineering Implementation Guide (AWS Ecosystem)

This operational guide provides the step-by-step engineering implementation code, Terraform IaC, OpenTelemetry (OTel) Collector configurations, Prometheus alerting rules, and Grafana dashboard specifications for **Part 1 – Infrastructure Observability**.

---

## 1. Architectural Overview & Component Topology

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                   AWS INFRASTRUCTURE                                      │
│    EC2  │  ECS  │  EKS  │  AWS Lambda  │  Amazon SageMaker  │  ALB  │  Amazon RDS / DynamoDB │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                       LOCAL AGENTS & CONTAINER INSTRUMENTATION                            │
│   CloudWatch Agent │ ADOT Agent / Sidecar │ Node Exporter │ DCGM Exporter │ cAdvisor       │
└──────────────────────────────┬────────────────────────────────────────────────────────────┘
                               │ (OTLP gRPC / Prometheus Remote Write)
                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                               OPENTELEMETRY GATEWAY CLUSTER                               │
│        Filtering • Attribute Enrichment • Memory Limiting • Batching • PII Redaction       │
└──────────────┬───────────────────────┬───────────────────────┬────────────────────────────┘
               │                       │                       │
               ▼                       ▼                       ▼
    ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
    │  Amazon CloudWatch │  │   Amazon Managed   │  │     AWS X-Ray      │
    │     (Metrics)      │  │     Prometheus     │  │      (Traces)      │
    └──────────┬─────────┘  └──────────┬─────────┘  └────────────────────┘
               │                       │
               └───────────┬───────────┘
                           ▼
            ┌─────────────────────────────┐
            │    Amazon Managed Grafana   │
            └──────────────┬──────────────┘
                           ▼
            ┌─────────────────────────────┐
            │    Alerting & Remediation   │
            │ CloudWatch Alarms / SNS /   │
            │ Alertmanager / Lambda / SSM │
            └─────────────────────────────┘
```

---

## 2. Step 1: IAM Roles & Least-Privilege Policy (Terraform)

Deploy the IAM role and policies for the ADOT Collector DaemonSet on AWS EKS using IAM Roles for Service Accounts (IRSA).

### `main.tf` (ADOT Collector IAM Setup)
```hcl
resource "aws_iam_role" "adot_collector_role" {
  name = "adot-collector-irsa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.eks_oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${var.eks_oidc_issuer_url}:sub" = "system:serviceaccount:monitoring:adot-collector-sa"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "adot_telemetry_policy" {
  name        = "ADOTTelemetryPermissionsPolicy"
  description = "Allows ADOT Collector to push metrics to AMP, CloudWatch, and X-Ray"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aps:RemoteWrite",
          "aps:GetSeries",
          "aps:GetLabels",
          "aps:GetMetricMetadata"
        ]
        Resource = "arn:aws:aps:${var.aws_region}:${var.aws_account_id}:workspace/*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:PutLogEvents",
          "logs:CreateLogStream",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "adot_attach" {
  role       = aws_iam_role.adot_collector_role.name
  policy_arn = aws_iam_policy.adot_telemetry_policy.arn
}
```

---

## 3. Step 2: OpenTelemetry Gateway Configuration (`otel-collector-config.yaml`)

Deploy the production OTel Collector Gateway configuration enforcing memory limits, PII regex scrubbing, batching, and dual export to AMP and CloudWatch.

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  prometheus:
    config:
      scrape_configs:
        - job_name: 'dcgm-gpu-exporter'
          scrape_interval: 5s
          static_configs:
            - targets: ['nvidia-dcgm-exporter.monitoring.svc.cluster.local:9400']

processors:
  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
    spike_limit_percentage: 20

  batch:
    send_batch_size: 8192
    timeout: 1s
    send_batch_max_size: 10240

  transform:
    error_mode: ignore
    log_statements:
      - context: log
        statements:
          - set(attributes["payload"], ReplaceAll(attributes["payload"], "\\b\\d{3}-\\d{2}-\\d{4}\\b", "[REDACTED_SSN]"))
          - set(attributes["payload"], ReplaceAll(attributes["payload"], "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b", "[REDACTED_EMAIL]"))

  resourcedetection:
    detectors: [env, ecs, ec2, eks]
    timeout: 2s
    override: false

exporters:
  prometheusremotewrite:
    endpoint: "https://aps-workspaces.${AWS_REGION}.amazonaws.com/workspaces/${WORKSPACE_ID}/api/v1/remote_write"
    aws_auth:
      region: "${AWS_REGION}"
      service: "aps"

  awscloudwatchlogs:
    log_group_name: "/aws/eks/infrastructure-observability"
    log_stream_name: "{PodName}"
    region: "${AWS_REGION}"

  awsxray:
    region: "${AWS_REGION}"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, transform, batch]
      exporters: [awsxray]
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, transform, batch]
      exporters: [awscloudwatchlogs]
```

---

## 4. Step 3: Prometheus Alerting Rules (`alerts.yml`)

Configure alerting rules for container compute, GPU memory saturation, and pod crashes.

```yaml
groups:
  - name: infrastructure_alerts
    rules:
      - alert: HighCPUUtilization
        expr: (sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod) / sum(kube_pod_container_resource_limits{resource="cpu"}) by (pod)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pod CPU utilization above 85% for {{ $labels.pod }}"

      - alert: GPUMemorySaturation
        expr: (DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE)) * 100 > 90
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "NVIDIA GPU VRAM utilization above 90% on GPU {{ $labels.gpu }}"

      - alert: PodCrashLoopBackOff
        expr: rate(kube_pod_container_status_restarts_total[5m]) * 300 > 2
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Pod {{ $labels.pod }} in CrashLoopBackOff"
```

---

## 5. Step 4: Verification & Automated Validation

Validate ADOT Collector deployment and metric ingestion via AWS CLI:

```bash
# Check EKS ADOT DaemonSet status
kubectl get pods -n monitoring -l app=adot-collector

# Verify Prometheus metric scrape using AWS CLI
aws amp query \
  --workspace-id ws-12345678-abcd-ef01-2345-6789abcdef01 \
  --query-string 'DCGM_FI_DEV_GPU_UTIL' \
  --region us-west-2
```
