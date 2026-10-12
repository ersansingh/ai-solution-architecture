data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  features = yamldecode(file(var.features_yaml_path))
  # Feature Group schema == config/features.yaml (same mapping as churn.feature_store.feature_types).
  feature_definitions = concat(
    [
      { name = local.features.record_identifier, type = "String" },
      { name = local.features.event_time, type = "String" },
    ],
    [for c in local.features.numeric : { name = c, type = "Fractional" }],
    [for c in keys(local.features.categorical) : { name = c, type = "String" }],
  )
}

# ---- SageMaker execution role (Studio, Processing, Training, Pipelines, Endpoints) ----
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${var.project}-sagemaker-execution"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

# Lab baseline from Phase 1; the bucket-scoped statements below replace AmazonS3FullAccess.
resource "aws_iam_role_policy_attachment" "sagemaker_full" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

data "aws_iam_policy_document" "execution" {
  statement {
    sid       = "DataLake"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket", "s3:GetBucketLocation"]
    resources = [var.bucket_arn, "${var.bucket_arn}/*"]
  }
  statement {
    sid       = "Kms"
    actions   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey*", "kms:DescribeKey", "kms:CreateGrant"]
    resources = [var.kms_key_arn]
  }
  statement {
    sid       = "FeatureStoreIngest"
    actions   = ["sagemaker:PutRecord", "sagemaker:GetRecord", "sagemaker:DescribeFeatureGroup"]
    resources = [aws_sagemaker_feature_group.customers.arn]
  }
  statement {
    sid = "OfflineStoreQuery"
    actions = [
      "athena:StartQueryExecution", "athena:GetQueryExecution", "athena:GetQueryResults",
      "glue:GetTable", "glue:GetDatabase", "glue:GetPartitions", "glue:CreateTable", "glue:UpdateTable",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "execution" {
  name   = "data-lake-and-features"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution.json
}

# ---- Model Registry ----
resource "aws_sagemaker_model_package_group" "churn" {
  model_package_group_name        = var.model_package_group_name
  model_package_group_description = "TeleConnect customer churn models (PipelineModel: sklearn preprocessor + XGBoost)"
  tags                            = var.tags
}

# ---- Feature Store (online for churn-api, offline for training + batch snapshots) ----
resource "aws_sagemaker_feature_group" "customers" {
  feature_group_name             = var.feature_group_name
  record_identifier_feature_name = local.features.record_identifier
  event_time_feature_name        = local.features.event_time
  role_arn                       = aws_iam_role.execution.arn
  description                    = "Customer profile, billing, usage, support and engineered churn features"

  dynamic "feature_definition" {
    for_each = local.feature_definitions
    content {
      feature_name = feature_definition.value.name
      feature_type = feature_definition.value.type
    }
  }

  online_store_config {
    enable_online_store = true
    security_config {
      kms_key_id = var.kms_key_arn
    }
  }

  offline_store_config {
    disable_glue_table_creation = false
    s3_storage_config {
      s3_uri     = "s3://${var.bucket_name}/feature-store"
      kms_key_id = var.kms_key_arn
    }
  }
  tags = var.tags
}

resource "aws_athena_workgroup" "churn" {
  name          = var.project
  force_destroy = true
  configuration {
    enforce_workgroup_configuration = true
    result_configuration {
      output_location = "s3://${var.bucket_name}/artifacts/athena/"
      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = var.kms_key_arn
      }
    }
  }
  tags = var.tags
}

# ---- Optional SageMaker Studio domain (Phase 1 Task 5) ----
resource "aws_sagemaker_domain" "studio" {
  count       = var.create_studio_domain ? 1 : 0
  domain_name = var.project
  auth_mode   = "IAM"
  vpc_id      = var.vpc_id
  subnet_ids  = var.private_subnet_ids
  kms_key_id  = var.kms_key_arn

  app_network_access_type = "VpcOnly"
  default_user_settings {
    execution_role = aws_iam_role.execution.arn
  }
  tags = var.tags
}

resource "aws_sagemaker_user_profile" "users" {
  for_each          = var.create_studio_domain ? toset(var.studio_users) : toset([])
  domain_id         = aws_sagemaker_domain.studio[0].id
  user_profile_name = each.value
  tags              = var.tags
}
