# Retraining triggers (R7, ADR-5), model approval -> deployment (ADR-6), pipeline failure alerts.
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  # Pipelines are upserted by pipelines/pipeline.py; the ARN uses the lower-cased name.
  pipeline_arn = "arn:aws:sagemaker:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:pipeline/${lower(var.pipeline_name)}"
  use_pipeline = var.retrain_target == "sagemaker_pipeline"
  target_arn   = local.use_pipeline ? local.pipeline_arn : var.retrain_queue_arn
  retrain_rules = {
    monthly  = aws_cloudwatch_event_rule.monthly.name
    manifest = aws_cloudwatch_event_rule.manifest.name
  }
}

resource "aws_cloudwatch_event_rule" "monthly" {
  name                = "${var.project}-monthly-retrain"
  description         = "First Sunday of the month, 02:00 UTC (Phase 9 Task 16)"
  schedule_expression = "cron(0 2 ? * SUN#1 *)"
  tags                = var.tags
}

resource "aws_cloudwatch_event_rule" "manifest" {
  name        = "${var.project}-new-data-retrain"
  description = "One retrain per data drop: _MANIFEST.json is written after all source files (ADR-5)"
  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [var.bucket_name] }
      object = { key = [{ suffix = "_MANIFEST.json" }] }
    }
  })
  tags = var.tags
}

data "aws_iam_policy_document" "events_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "events" {
  name               = "${var.project}-events"
  assume_role_policy = data.aws_iam_policy_document.events_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "events" {
  dynamic "statement" {
    for_each = local.use_pipeline ? [1] : []
    content {
      actions   = ["sagemaker:StartPipelineExecution"]
      resources = [local.pipeline_arn]
    }
  }
  dynamic "statement" {
    for_each = var.deploy_state_machine_arn == null ? [] : [1]
    content {
      actions   = ["states:StartExecution"]
      resources = [var.deploy_state_machine_arn]
    }
  }
  dynamic "statement" {
    for_each = local.use_pipeline ? [] : [1]
    content {
      actions   = ["sqs:SendMessage"]
      resources = [var.retrain_queue_arn]
    }
  }
}

resource "aws_iam_role_policy" "events" {
  name   = "targets"
  role   = aws_iam_role.events.id
  policy = data.aws_iam_policy_document.events.json
}

resource "aws_cloudwatch_event_target" "retrain" {
  for_each = local.retrain_rules
  rule     = each.value
  arn      = local.target_arn
  role_arn = local.use_pipeline ? aws_iam_role.events.arn : null

  dynamic "sagemaker_pipeline_target" {
    for_each = local.use_pipeline ? [1] : []
    content {
      pipeline_parameter_list {
        name  = "GitSha"
        value = "eventbridge-${each.key}"
      }
    }
  }
}

# ---- Model approved in the registry -> deploy state machine ----
resource "aws_cloudwatch_event_rule" "approved" {
  count       = var.deploy_state_machine_arn == null ? 0 : 1
  name        = "${var.project}-model-approved"
  description = "Model package approved in ${var.model_package_group_name}"
  event_pattern = jsonencode({
    source      = ["aws.sagemaker"]
    detail-type = ["SageMaker Model Package State Change"]
    detail = {
      ModelPackageGroupName = [var.model_package_group_name]
      ModelApprovalStatus   = ["Approved"]
    }
  })
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "approved" {
  count    = var.deploy_state_machine_arn == null ? 0 : 1
  rule     = aws_cloudwatch_event_rule.approved[0].name
  arn      = var.deploy_state_machine_arn
  role_arn = aws_iam_role.events.arn
}

# ---- Pipeline execution failed -> SNS ----
resource "aws_cloudwatch_event_rule" "pipeline_failed" {
  name = "${var.project}-pipeline-failed"
  event_pattern = jsonencode({
    source      = ["aws.sagemaker"]
    detail-type = ["SageMaker Model Building Pipeline Execution Status Change"]
    detail      = { currentPipelineExecutionStatus = ["Failed"] }
  })
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "pipeline_failed" {
  rule = aws_cloudwatch_event_rule.pipeline_failed.name
  arn  = var.sns_topic_arn
}
