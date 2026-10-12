# LocalStack (Community) environment: the AWS-native pieces that LocalStack emulates, built from the
# SAME modules as envs/aws. SageMaker, EKS, API Gateway VPC links and Feature Store are not emulated
# by Community edition; locally they are replaced by:
#   SageMaker endpoint      -> services/model-server (same /ping + /invocations contract)
#   Feature Store online    -> DynamoDB table (churn-api FEATURE_BACKEND=dynamodb)
#   SageMaker Pipeline      -> SQS queue that records retrain triggers (asserted by integration tests)
#   EKS                     -> docker-compose service, or k3d with deploy/helm/churn-api/values-local.yaml
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

variable "localstack_endpoint" {
  type    = string
  default = "http://localhost:4566"
}

variable "bucket_name" {
  type    = string
  default = "teleconnect-churn-local"
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    cloudwatch = var.localstack_endpoint
    dynamodb   = var.localstack_endpoint
    events     = var.localstack_endpoint
    iam        = var.localstack_endpoint
    kms        = var.localstack_endpoint
    s3         = var.localstack_endpoint
    sns        = var.localstack_endpoint
    sqs        = var.localstack_endpoint
    ssm        = var.localstack_endpoint
    sts        = var.localstack_endpoint
  }
}

locals {
  project       = "teleconnect-churn"
  features_yaml = abspath("${path.module}/../../../../config/features.yaml")
  tags          = { project = local.project, env = "local" }
}

module "data_lake" {
  source        = "../../modules/data_lake"
  project       = local.project
  bucket_name   = var.bucket_name
  force_destroy = true
  enforce_tls   = false
  tags          = local.tags
}

module "monitoring" {
  source             = "../../modules/monitoring"
  project            = local.project
  region             = "us-east-1"
  features_yaml_path = local.features_yaml
  create_api_alarms  = false
  create_dashboard   = false
  monthly_budget_usd = 0
  tags               = local.tags
}

resource "aws_sqs_queue" "retrain_triggers" {
  name = "${local.project}-retrain-triggers"
  tags = local.tags
}

resource "aws_sqs_queue_policy" "retrain_triggers" {
  queue_url = aws_sqs_queue.retrain_triggers.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.retrain_triggers.arn
    }]
  })
}

module "events" {
  source            = "../../modules/events"
  project           = local.project
  bucket_name       = module.data_lake.bucket_name
  retrain_target    = "sqs"
  retrain_queue_arn = aws_sqs_queue.retrain_triggers.arn
  sns_topic_arn     = module.monitoring.sns_topic_arn
  tags              = local.tags
}

resource "aws_dynamodb_table" "online_features" {
  name         = "teleconnect-online-features"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "customer_id"
  attribute {
    name = "customer_id"
    type = "S"
  }
  tags = local.tags
}

resource "aws_ssm_parameter" "serving_config" {
  name  = "/${local.project}/prod/serving-config"
  type  = "String"
  value = jsonencode({ endpoint_name = "local-model-server", threshold = 0.5, model_version = "none", source = "terraform-bootstrap" })
  lifecycle {
    ignore_changes = [value]
  }
}

output "bucket_name" {
  value = module.data_lake.bucket_name
}

output "retrain_queue_url" {
  value = aws_sqs_queue.retrain_triggers.id
}

output "sns_topic_arn" {
  value = module.monitoring.sns_topic_arn
}
