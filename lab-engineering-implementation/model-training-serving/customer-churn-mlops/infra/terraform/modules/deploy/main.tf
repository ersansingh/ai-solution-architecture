# Approved model package -> Step Functions -> Lambdas (deployment/lambdas/handlers.py) -> SageMaker endpoints.
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  account   = data.aws_caller_identity.current.account_id
  region    = data.aws_region.current.name
  functions = toset(["deploy_endpoint", "endpoint_status", "configure_autoscaling", "smoke_test", "publish_serving_config"])
  stage_config = {
    staging = {
      endpoint_name = var.staging_endpoint_name, instance_type = var.endpoint_instance_type, instance_count = 1,
      min_capacity  = 1, max_capacity = 1, target_invocations = var.target_invocations_per_instance,
      strategy      = "rolling", capture_pct = 100, rollback_alarms = []
    }
    prod = {
      endpoint_name  = var.prod_endpoint_name, instance_type = var.endpoint_instance_type,
      instance_count = var.prod_min_instances, min_capacity = var.prod_min_instances,
      max_capacity   = var.prod_max_instances, target_invocations = var.target_invocations_per_instance,
      strategy       = "blue_green_canary", capture_pct = var.prod_capture_pct, rollback_alarms = var.rollback_alarm_names
    }
  }
}

data "archive_file" "lambdas" {
  type        = "zip"
  source_dir  = var.lambda_source_dir
  output_path = "${path.module}/.build/deploy-lambdas.zip"
  excludes    = ["__pycache__"]
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.project}-deploy-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid = "Endpoints"
    actions = [
      "sagemaker:CreateModel", "sagemaker:CreateEndpointConfig", "sagemaker:CreateEndpoint",
      "sagemaker:UpdateEndpoint", "sagemaker:DescribeEndpoint", "sagemaker:DescribeEndpointConfig",
      "sagemaker:AddTags", "sagemaker:InvokeEndpoint",
    ]
    resources = [
      "arn:aws:sagemaker:${local.region}:${local.account}:model/churn-*",
      "arn:aws:sagemaker:${local.region}:${local.account}:endpoint-config/churn-*",
      "arn:aws:sagemaker:${local.region}:${local.account}:endpoint/customer-churn-*",
    ]
  }
  statement {
    sid       = "Registry"
    actions   = ["sagemaker:DescribeModelPackage"]
    resources = ["arn:aws:sagemaker:${local.region}:${local.account}:model-package/*"]
  }
  statement {
    sid       = "PassEndpointRole"
    actions   = ["iam:PassRole"]
    resources = [var.endpoint_role_arn]
  }
  statement {
    sid = "AutoScaling"
    actions = [
      "application-autoscaling:RegisterScalableTarget", "application-autoscaling:DeregisterScalableTarget",
      "application-autoscaling:DescribeScalableTargets", "application-autoscaling:PutScalingPolicy",
      "cloudwatch:PutMetricAlarm", "cloudwatch:DescribeAlarms", "cloudwatch:DeleteAlarms",
    ]
    resources = ["*"]
  }
  statement {
    sid       = "AutoScalingServiceLinkedRole"
    actions   = ["iam:CreateServiceLinkedRole"]
    resources = ["arn:aws:iam::${local.account}:role/aws-service-role/sagemaker.application-autoscaling.amazonaws.com/*"]
  }
  statement {
    sid       = "Artifacts"
    actions   = ["s3:GetObject"]
    resources = ["${var.bucket_arn}/*"]
  }
  statement {
    sid       = "Kms"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey*", "kms:CreateGrant", "kms:DescribeKey"]
    resources = [var.kms_key_arn]
  }
  statement {
    sid       = "ServingConfig"
    actions   = ["ssm:PutParameter", "ssm:GetParameter"]
    resources = ["arn:aws:ssm:${local.region}:${local.account}:parameter/${var.project}/*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "deploy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda.json
}

resource "aws_lambda_function" "this" {
  for_each         = local.functions
  function_name    = "${var.project}-${replace(each.value, "_", "-")}"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handlers.${each.value}"
  filename         = data.archive_file.lambdas.output_path
  source_code_hash = data.archive_file.lambdas.output_base64sha256
  timeout          = each.value == "smoke_test" ? 300 : 60
  memory_size      = 256

  environment {
    variables = {
      STAGE_CONFIG             = jsonencode(local.stage_config)
      ENDPOINT_ROLE_ARN        = var.endpoint_role_arn
      DATA_CAPTURE_S3_URI      = "s3://${var.bucket_name}/monitoring/data-capture"
      DATA_BUCKET              = var.bucket_name
      KMS_KEY_ARN              = var.kms_key_arn
      SERVING_CONFIG_PARAMETER = "/${var.project}/{stage}/serving-config"
      LATENCY_BUDGET_MS        = "150"
    }
  }
  tags = var.tags
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each          = aws_lambda_function.this
  name              = "/aws/lambda/${each.value.function_name}"
  retention_in_days = 30
}

# ---- serving config parameters (written by publish_serving_config, read by churn-api) ----
resource "aws_ssm_parameter" "serving_config" {
  for_each = local.stage_config
  name     = "/${var.project}/${each.key}/serving-config"
  type     = "String"
  value = jsonencode({
    endpoint_name = each.value.endpoint_name, threshold = 0.5, model_version = "none", source = "terraform-bootstrap"
  })
  lifecycle {
    ignore_changes = [value]
  }
  tags = var.tags
}

# ---- state machine ----
data "aws_iam_policy_document" "sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn" {
  name               = "${var.project}-deploy-sfn"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "sfn" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [for f in aws_lambda_function.this : f.arn]
  }
  statement {
    actions   = ["sns:Publish"]
    resources = [var.sns_topic_arn]
  }
  statement {
    actions = [
      "logs:CreateLogDelivery", "logs:GetLogDelivery", "logs:UpdateLogDelivery", "logs:DeleteLogDelivery",
      "logs:ListLogDeliveries", "logs:PutResourcePolicy", "logs:DescribeResourcePolicies", "logs:DescribeLogGroups",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "sfn" {
  name   = "deploy"
  role   = aws_iam_role.sfn.id
  policy = data.aws_iam_policy_document.sfn.json
}

resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/vendedlogs/states/${var.project}-deploy"
  retention_in_days = 30
}

resource "aws_sfn_state_machine" "deploy" {
  name     = "${var.project}-deploy"
  role_arn = aws_iam_role.sfn.arn
  definition = templatefile(var.state_machine_definition_path, {
    deploy_fn     = aws_lambda_function.this["deploy_endpoint"].arn
    status_fn     = aws_lambda_function.this["endpoint_status"].arn
    autoscale_fn  = aws_lambda_function.this["configure_autoscaling"].arn
    smoke_fn      = aws_lambda_function.this["smoke_test"].arn
    publish_fn    = aws_lambda_function.this["publish_serving_config"].arn
    sns_topic_arn = var.sns_topic_arn
  })
  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }
  tags = var.tags
}
