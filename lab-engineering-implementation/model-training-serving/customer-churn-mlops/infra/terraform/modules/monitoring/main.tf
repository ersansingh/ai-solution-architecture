# Plan section 6.6. Alarm -> SNS "customer-churn-alerts" -> email (ML Eng, Platform, Ops).
# The two *-rollback alarms are wired into the prod endpoint's AutoRollbackConfiguration.

locals {
  features = yamldecode(file(var.features_yaml_path))
  # Model Monitor baselines are headerless CSV, so drift metrics are named after column positions.
  # Numeric features come first in the endpoint payload (churn.config.model_input_columns).
  drift_metric  = { for f in var.drift_features : f => "feature_baseline_drift__c${index(local.features.numeric, f)}" }
  endpoint_dims = { EndpointName = var.endpoint_name, VariantName = var.variant_name }
  api_dims      = { ApiName = var.api_name, Stage = var.api_stage }
  app_dims      = { Service = "churn-api", Stage = "prod" }
  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_sns_topic" "alerts" {
  name              = var.topic_name
  kms_master_key_id = var.sns_kms_key_id
  tags              = var.tags
}

data "aws_iam_policy_document" "topic" {
  statement {
    sid     = "AllowCloudWatchAndEventBridge"
    actions = ["sns:Publish"]
    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com", "events.amazonaws.com"]
    }
    resources = [aws_sns_topic.alerts.arn]
  }
}

resource "aws_sns_topic_policy" "alerts" {
  arn    = aws_sns_topic.alerts.arn
  policy = data.aws_iam_policy_document.topic.json
}

resource "aws_sns_topic_subscription" "email" {
  for_each  = toset(var.alert_emails)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = each.value
}

# ---- latency ----
resource "aws_cloudwatch_metric_alarm" "api_latency" {
  count               = var.create_api_alarms ? 1 : 0
  alarm_name          = "churn-api-gateway-latency-p99"
  alarm_description   = "End-to-end p99 latency at API Gateway above the 150 ms SLA (R5)"
  namespace           = "AWS/ApiGateway"
  metric_name         = "Latency"
  dimensions          = local.api_dims
  extended_statistic  = "p99"
  period              = 60
  evaluation_periods  = 5
  datapoints_to_alarm = 3
  threshold           = 150
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
  ok_actions          = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "service_latency" {
  alarm_name          = "churn-api-service-latency-p99"
  alarm_description   = "churn-api (EKS) p99 latency incl. Feature Store + endpoint above 150 ms"
  namespace           = var.app_metrics_namespace
  metric_name         = "EndToEndLatency"
  dimensions          = local.app_dims
  extended_statistic  = "p99"
  period              = 60
  evaluation_periods  = 5
  datapoints_to_alarm = 3
  threshold           = 150
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "model_latency" {
  alarm_name          = "churn-prod-model-latency-p99"
  alarm_description   = "Model latency budget (50 ms). ModelLatency is reported in MICROSECONDS (plan G13)."
  namespace           = "AWS/SageMaker"
  metric_name         = "ModelLatency"
  dimensions          = local.endpoint_dims
  extended_statistic  = "p99"
  period              = 60
  evaluation_periods  = 5
  datapoints_to_alarm = 3
  threshold           = 50000
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

# ---- errors ----
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  count               = var.create_api_alarms ? 1 : 0
  alarm_name          = "churn-api-gateway-5xx-rate"
  namespace           = "AWS/ApiGateway"
  metric_name         = "5XXError"
  dimensions          = local.api_dims
  statistic           = "Average"
  period              = 60
  evaluation_periods  = 5
  datapoints_to_alarm = 3
  threshold           = 0.02
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "endpoint_errors" {
  alarm_name          = "churn-prod-endpoint-5xx-rate"
  alarm_description   = "Endpoint 5XX > 2% of invocations"
  evaluation_periods  = 5
  datapoints_to_alarm = 3
  threshold           = 0.02
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions

  metric_query {
    id          = "rate"
    expression  = "IF(invocations > 0, errors / invocations, 0)"
    label       = "5XX rate"
    return_data = true
  }
  metric_query {
    id = "errors"
    metric {
      namespace   = "AWS/SageMaker"
      metric_name = "Invocation5XXErrors"
      dimensions  = local.endpoint_dims
      period      = 60
      stat        = "Sum"
    }
  }
  metric_query {
    id = "invocations"
    metric {
      namespace   = "AWS/SageMaker"
      metric_name = "Invocations"
      dimensions  = local.endpoint_dims
      period      = 60
      stat        = "Sum"
    }
  }
}

# ---- deployment guardrails (Phase 10 Task 10: error > 5%, latency > 300 ms) ----
resource "aws_cloudwatch_metric_alarm" "rollback_5xx" {
  alarm_name          = "churn-prod-5xx-rollback"
  alarm_description   = "Blue/green auto-rollback: endpoint 5XX > 5%"
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 0.05
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions

  metric_query {
    id          = "rate"
    expression  = "IF(invocations > 0, errors / invocations, 0)"
    return_data = true
  }
  metric_query {
    id = "errors"
    metric {
      namespace   = "AWS/SageMaker"
      metric_name = "Invocation5XXErrors"
      dimensions  = local.endpoint_dims
      period      = 60
      stat        = "Sum"
    }
  }
  metric_query {
    id = "invocations"
    metric {
      namespace   = "AWS/SageMaker"
      metric_name = "Invocations"
      dimensions  = local.endpoint_dims
      period      = 60
      stat        = "Sum"
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "rollback_latency" {
  alarm_name          = "churn-prod-latency-rollback"
  alarm_description   = "Blue/green auto-rollback: model p99 latency > 300 ms (300000 us)"
  namespace           = "AWS/SageMaker"
  metric_name         = "ModelLatency"
  dimensions          = local.endpoint_dims
  extended_statistic  = "p99"
  period              = 60
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 300000
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

# ---- capacity ----
resource "aws_cloudwatch_metric_alarm" "cpu" {
  alarm_name          = "churn-prod-endpoint-cpu"
  alarm_description   = "Endpoint CPU high for 15 min (CPUUtilization is summed over vCPUs: 80% x vCPUs)"
  namespace           = "/aws/sagemaker/Endpoints"
  metric_name         = "CPUUtilization"
  dimensions          = local.endpoint_dims
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = var.cpu_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

# ---- model quality signals ----
resource "aws_cloudwatch_metric_alarm" "feature_drift" {
  for_each            = local.drift_metric
  alarm_name          = "churn-drift-${each.key}"
  alarm_description   = "Model Monitor drift distance for ${each.key} (${each.value}) above ${var.drift_threshold}"
  namespace           = "aws/sagemaker/Endpoints/data-metrics"
  metric_name         = each.value
  dimensions          = { Endpoint = var.endpoint_name, MonitoringSchedule = "${var.endpoint_name}-data-quality" }
  statistic           = "Maximum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = var.drift_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "prediction_high" {
  alarm_name          = "churn-prediction-distribution-high"
  alarm_description   = "Mean predicted churn above training rate + 5pp (early warning while labels lag 90 days)"
  namespace           = var.app_metrics_namespace
  metric_name         = "MeanPredictedChurnRate"
  dimensions          = local.app_dims
  statistic           = "Average"
  period              = 3600
  evaluation_periods  = 3
  threshold           = var.training_churn_rate + 0.05
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "prediction_low" {
  alarm_name          = "churn-prediction-distribution-low"
  namespace           = var.app_metrics_namespace
  metric_name         = "MeanPredictedChurnRate"
  dimensions          = local.app_dims
  statistic           = "Average"
  period              = 3600
  evaluation_periods  = 3
  threshold           = var.training_churn_rate - 0.05
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "model_quality_auc" {
  alarm_name          = "churn-model-quality-auc"
  alarm_description   = "Ground-truth AUC from Model Monitor (model quality) below 0.88"
  namespace           = "aws/sagemaker/Endpoints/model-metrics"
  metric_name         = "auc"
  dimensions          = { Endpoint = var.endpoint_name, MonitoringSchedule = "${var.endpoint_name}-model-quality" }
  statistic           = "Minimum"
  period              = 86400
  evaluation_periods  = 1
  threshold           = 0.88
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_actions
}

# ---- dashboard ----
resource "aws_cloudwatch_dashboard" "ops" {
  count          = var.create_dashboard ? 1 : 0
  dashboard_name = "TeleConnect-Churn-Ops"
  dashboard_body = jsonencode({
    widgets = [
      { type = "metric", x = 0, y = 0, width = 12, height = 6, properties = {
        title = "Invocations", region = var.region, stat = "Sum", period = 60,
        metrics = [["AWS/SageMaker", "Invocations", "EndpointName", var.endpoint_name, "VariantName", var.variant_name],
        [var.app_metrics_namespace, "Predictions", "Service", "churn-api", "Stage", "prod"]]
      } },
      { type = "metric", x = 12, y = 0, width = 12, height = 6, properties = {
        title = "Latency p50 / p99 (ms)", region = var.region, period = 60,
        metrics = [["AWS/ApiGateway", "Latency", "ApiName", var.api_name, "Stage", var.api_stage, { stat = "p99" }],
          [var.app_metrics_namespace, "EndToEndLatency", "Service", "churn-api", "Stage", "prod", { stat = "p99" }],
          [var.app_metrics_namespace, "EndToEndLatency", "Service", "churn-api", "Stage", "prod", { stat = "p50" }],
          [{ expression = "m1 / 1000", label = "ModelLatency p99 (ms)", id = "e1" }],
        ["AWS/SageMaker", "ModelLatency", "EndpointName", var.endpoint_name, "VariantName", var.variant_name, { stat = "p99", id = "m1", visible = false }]]
      } },
      { type = "metric", x = 0, y = 6, width = 8, height = 6, properties = {
        title = "Errors", region = var.region, stat = "Sum", period = 60,
        metrics = [["AWS/SageMaker", "Invocation5XXErrors", "EndpointName", var.endpoint_name, "VariantName", var.variant_name],
          ["AWS/SageMaker", "Invocation4XXErrors", "EndpointName", var.endpoint_name, "VariantName", var.variant_name],
        [var.app_metrics_namespace, "Errors", "Service", "churn-api", "Stage", "prod"]]
      } },
      { type = "metric", x = 8, y = 6, width = 8, height = 6, properties = {
        title = "CPU / memory / instances", region = var.region, stat = "Average", period = 300,
        metrics = [["/aws/sagemaker/Endpoints", "CPUUtilization", "EndpointName", var.endpoint_name, "VariantName", var.variant_name],
          ["/aws/sagemaker/Endpoints", "MemoryUtilization", "EndpointName", var.endpoint_name, "VariantName", var.variant_name],
        ["/aws/sagemaker/Endpoints", "InstanceCount", "EndpointName", var.endpoint_name, "VariantName", var.variant_name, { yAxis = "right" }]]
      } },
      { type = "metric", x = 16, y = 6, width = 8, height = 6, properties = {
        title = "Prediction distribution", region = var.region, stat = "Average", period = 3600,
        metrics = [[var.app_metrics_namespace, "MeanPredictedChurnRate", "Service", "churn-api", "Stage", "prod"],
        [var.app_metrics_namespace, "ChurnFlagRate", "Service", "churn-api", "Stage", "prod"]]
      } },
      { type = "metric", x = 0, y = 12, width = 24, height = 6, properties = {
        title = "Feature drift (Model Monitor)", region = var.region, stat = "Maximum", period = 3600,
        metrics = [for f, m in local.drift_metric : ["aws/sagemaker/Endpoints/data-metrics", m, "Endpoint", var.endpoint_name,
        "MonitoringSchedule", "${var.endpoint_name}-data-quality", { label = f }]]
      } },
      { type = "alarm", x = 0, y = 18, width = 24, height = 4, properties = {
        title = "Alarms",
        alarms = concat([aws_cloudwatch_metric_alarm.service_latency.arn, aws_cloudwatch_metric_alarm.model_latency.arn,
          aws_cloudwatch_metric_alarm.endpoint_errors.arn, aws_cloudwatch_metric_alarm.rollback_5xx.arn,
          aws_cloudwatch_metric_alarm.rollback_latency.arn, aws_cloudwatch_metric_alarm.prediction_high.arn,
        aws_cloudwatch_metric_alarm.model_quality_auc.arn], [for a in aws_cloudwatch_metric_alarm.feature_drift : a.arn])
      } },
    ]
  })
}

resource "aws_budgets_budget" "project" {
  count        = var.monthly_budget_usd > 0 ? 1 : 0
  name         = "${var.project}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = [format("user:project$%s", var.project)]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.alert_emails
  }
}
