terraform {
  required_version = ">= 1.6"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.60" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
  # Configure a remote backend (S3 + DynamoDB lock) per environment before first apply.
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = var.project, Environment = var.environment, ManagedBy = "terraform" }
  }
}

data "aws_caller_identity" "current" {}

locals {
  name = "${var.project}-${var.environment}"
}

# ───────────── Encryption ─────────────
resource "aws_kms_key" "data" {
  description             = "${local.name} data key (S3, SQS, Aurora, DynamoDB)"
  enable_key_rotation     = true
  deletion_window_in_days = 14
}

resource "aws_kms_alias" "data" {
  name          = "alias/${local.name}-data"
  target_key_id = aws_kms_key.data.key_id
}

# ───────────── Network ─────────────
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${local.name}-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  availability_zone       = var.azs[count.index]
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  map_public_ip_on_launch = false
  tags                    = { Name = "${local.name}-public-${count.index}" }
}

resource "aws_subnet" "app" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  availability_zone = var.azs[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 10 + count.index)
  tags              = { Name = "${local.name}-app-${count.index}" }
}

resource "aws_subnet" "data" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  availability_zone = var.azs[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 20 + count.index)
  tags              = { Name = "${local.name}-data-${count.index}" }
}

resource "aws_eip" "nat" {
  count  = 2
  domain = "vpc"
}

resource "aws_nat_gateway" "nat" {
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  depends_on    = [aws_internet_gateway.igw]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "app" {
  count  = 2
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat[count.index].id
  }
}

resource "aws_route_table_association" "app" {
  count          = 2
  subnet_id      = aws_subnet.app[count.index].id
  route_table_id = aws_route_table.app[count.index].id
}

resource "aws_security_group" "app" {
  name_prefix = "${local.name}-app-"
  vpc_id      = aws_vpc.main.id
  egress {
    description = "HTTPS egress (AWS endpoints, Drive API)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db" {
  name_prefix = "${local.name}-db-"
  vpc_id      = aws_vpc.main.id
  ingress {
    description     = "PostgreSQL from app tier only"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}

# Gateway endpoint keeps S3 traffic off the NAT gateways
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.app[*].id
}

resource "aws_vpc_flow_log" "main" {
  vpc_id               = aws_vpc.main.id
  traffic_type         = "ALL"
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.flow.arn
  iam_role_arn         = aws_iam_role.flow.arn
}

resource "aws_cloudwatch_log_group" "flow" {
  name              = "/${local.name}/vpc-flow"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.data.arn
}

resource "aws_iam_role" "flow" {
  name = "${local.name}-flow-logs"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "vpc-flow-logs.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy" "flow" {
  role = aws_iam_role.flow.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"], Resource = "${aws_cloudwatch_log_group.flow.arn}:*" }]
  })
}

# ───────────── Storage ─────────────
resource "random_id" "suffix" {
  byte_length = 3
}

resource "aws_s3_bucket" "raw" {
  bucket = "${local.name}-raw-${random_id.suffix.hex}"
}

resource "aws_s3_bucket" "evidence" {
  bucket              = "${local.name}-evidence-${random_id.suffix.hex}"
  object_lock_enabled = true
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_versioning" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_object_lock_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  rule {
    default_retention {
      mode = "GOVERNANCE" # switch to COMPLIANCE once the audit-retention policy is approved
      days = var.evidence_retention_days
    }
  }
  depends_on = [aws_s3_bucket_versioning.evidence]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "enc" {
  for_each = { raw = aws_s3_bucket.raw.id, evidence = aws_s3_bucket.evidence.id }
  bucket   = each.value
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "block" {
  for_each                = { raw = aws_s3_bucket.raw.id, evidence = aws_s3_bucket.evidence.id }
  bucket                  = each.value
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    id     = "tiering"
    status = "Enabled"
    filter {}
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    noncurrent_version_expiration { noncurrent_days = 365 }
  }
}

# ───────────── Queueing & idempotency ─────────────
resource "aws_sqs_queue" "dlq" {
  name                      = "${local.name}-intake-dlq"
  kms_master_key_id         = aws_kms_key.data.id
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "intake" {
  name                       = "${local.name}-intake"
  kms_master_key_id          = aws_kms_key.data.id
  visibility_timeout_seconds = 300
  redrive_policy             = jsonencode({ deadLetterTargetArn = aws_sqs_queue.dlq.arn, maxReceiveCount = 5 })
}

resource "aws_dynamodb_table" "idempotency" {
  name         = "${local.name}-idempotency"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "idempotency_key" # sha256(document) + "#" + rule/policy version
  attribute {
    name = "idempotency_key"
    type = "S"
  }
  point_in_time_recovery { enabled = true }
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.data.arn
  }
}

# ───────────── Results database ─────────────
resource "aws_db_subnet_group" "data" {
  name       = "${local.name}-data"
  subnet_ids = aws_subnet.data[*].id
}

resource "aws_rds_cluster" "results" {
  cluster_identifier          = "${local.name}-results"
  engine                      = "aurora-postgresql"
  engine_mode                 = "provisioned"
  database_name               = "reconciliation"
  master_username             = "recon_admin"
  manage_master_user_password = true # password lives in Secrets Manager, not in state files or code
  db_subnet_group_name        = aws_db_subnet_group.data.name
  vpc_security_group_ids      = [aws_security_group.db.id]
  storage_encrypted           = true
  kms_key_id                  = aws_kms_key.data.arn
  backup_retention_period     = 14
  deletion_protection         = var.environment == "prod"
  skip_final_snapshot         = var.environment != "prod"
  final_snapshot_identifier   = var.environment == "prod" ? "${local.name}-final" : null
  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 4
  }
}

resource "aws_rds_cluster_instance" "results" {
  count              = 2
  identifier         = "${local.name}-results-${count.index}"
  cluster_identifier = aws_rds_cluster.results.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.results.engine
}

# ───────────── Compute (ECS Fargate reconciler) ─────────────
resource "aws_ecs_cluster" "main" {
  name = local.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/${local.name}/reconciler"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.data.arn
}

resource "aws_iam_role" "task_exec" {
  name = "${local.name}-task-exec"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "task_exec" {
  role       = aws_iam_role.task_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name = "${local.name}-task"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

# Least privilege: read raw, write evidence, use queue/table/key, call Textract and Bedrock. No payment or ledger permissions exist anywhere.
resource "aws_iam_role_policy" "task" {
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject"], Resource = "${aws_s3_bucket.raw.arn}/*" },
      { Effect = "Allow", Action = ["s3:PutObject"], Resource = "${aws_s3_bucket.evidence.arn}/*" },
      { Effect = "Allow", Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = aws_sqs_queue.intake.arn },
      { Effect = "Allow", Action = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem"], Resource = aws_dynamodb_table.idempotency.arn },
      { Effect = "Allow", Action = ["kms:Decrypt", "kms:GenerateDataKey"], Resource = aws_kms_key.data.arn },
      { Effect = "Allow", Action = ["textract:AnalyzeExpense", "textract:AnalyzeDocument"], Resource = "*" },
      { Effect = "Allow", Action = ["bedrock:InvokeModel"], Resource = "arn:aws:bedrock:${var.region}::foundation-model/*" },
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = aws_rds_cluster.results.master_user_secret[0].secret_arn },
    ]
  })
}

resource "aws_ecs_task_definition" "reconciler" {
  family                   = "${local.name}-reconciler"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.task_exec.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions = jsonencode([{
    name      = "reconciler"
    image     = var.container_image
    essential = true
    environment = [
      { name = "INTAKE_QUEUE_URL", value = aws_sqs_queue.intake.url },
      { name = "IDEMPOTENCY_TABLE", value = aws_dynamodb_table.idempotency.name },
      { name = "RAW_BUCKET", value = aws_s3_bucket.raw.bucket },
      { name = "EVIDENCE_BUCKET", value = aws_s3_bucket.evidence.bucket },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options   = { awslogs-group = aws_cloudwatch_log_group.app.name, awslogs-region = var.region, awslogs-stream-prefix = "app" }
    }
  }])
}

resource "aws_ecs_service" "reconciler" {
  name            = "reconciler"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.reconciler.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = aws_subnet.app[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }
}

# ───────────── Monitoring & cost control ─────────────
resource "aws_sns_topic" "alerts" {
  name              = "${local.name}-alerts"
  kms_master_key_id = aws_kms_key.data.id
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "dlq_not_empty" {
  alarm_name          = "${local.name}-dlq-not-empty"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.dlq.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "queue_age" {
  alarm_name          = "${local.name}-intake-queue-age"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateAgeOfOldestMessage"
  dimensions          = { QueueName = aws_sqs_queue.intake.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 3
  threshold           = 3600 # PLACEHOLDER: agree latency SLO with the business
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_budgets_budget" "monthly" {
  name         = "${local.name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}

resource "aws_cloudtrail" "audit" {
  name                          = "${local.name}-trail"
  s3_bucket_name                = aws_s3_bucket.evidence.id
  s3_key_prefix                 = "cloudtrail"
  is_multi_region_trail         = false
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.data.arn
  include_global_service_events = true
  depends_on                    = [aws_s3_bucket_policy.cloudtrail]
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  bucket = aws_s3_bucket.evidence.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Sid = "AclCheck", Effect = "Allow", Principal = { Service = "cloudtrail.amazonaws.com" }, Action = "s3:GetBucketAcl", Resource = aws_s3_bucket.evidence.arn },
      { Sid = "Write", Effect = "Allow", Principal = { Service = "cloudtrail.amazonaws.com" }, Action = "s3:PutObject",
      Resource = "${aws_s3_bucket.evidence.arn}/cloudtrail/AWSLogs/${data.aws_caller_identity.current.account_id}/*", Condition = { StringEquals = { "s3:x-amz-acl" = "bucket-owner-full-control" } } },
    ]
  })
}
