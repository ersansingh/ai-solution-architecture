# Client -> API Gateway (REST, API key, throttling, validation) -> VPC Link -> internal NLB
#        -> churn-api pods on EKS (TargetGroupBinding from the Helm chart, target type ip).

resource "aws_security_group" "nlb" {
  name_prefix = "${var.name}-nlb-"
  description = "Internal NLB in front of churn-api"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from the VPC (API Gateway VPC link ENIs)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  egress {
    description = "To churn-api pods"
    from_port   = var.target_port
    to_port     = var.target_port
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  tags = var.tags
}

resource "aws_lb" "this" {
  name                             = "${var.name}-nlb"
  internal                         = true
  load_balancer_type               = "network"
  subnets                          = var.private_subnet_ids
  security_groups                  = [aws_security_group.nlb.id]
  enable_cross_zone_load_balancing = true
  # REST API VPC links reach the NLB over PrivateLink; SG rules can't match that traffic.
  enforce_security_group_inbound_rules_on_private_link_traffic = "off"
  tags                                                         = var.tags
}

resource "aws_lb_target_group" "this" {
  name                 = "${var.name}-tg"
  port                 = var.target_port
  protocol             = "TCP"
  target_type          = "ip"
  vpc_id               = var.vpc_id
  deregistration_delay = 30

  health_check {
    protocol            = "HTTP"
    path                = "/readyz"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 10
  }
  tags = var.tags
}

resource "aws_lb_listener" "this" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "TCP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

resource "aws_api_gateway_vpc_link" "this" {
  name        = "${var.name}-vpc-link"
  target_arns = [aws_lb.this.arn]
  tags        = var.tags
}

resource "aws_api_gateway_rest_api" "this" {
  name        = "${var.name}-api"
  description = "TeleConnect churn prediction API"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  tags = var.tags
}

resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = "v1"
}

resource "aws_api_gateway_resource" "predict" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "predict"
}

resource "aws_api_gateway_model" "predict_request" {
  rest_api_id  = aws_api_gateway_rest_api.this.id
  name         = "PredictRequest"
  content_type = "application/json"
  schema = jsonencode({
    "$schema"            = "http://json-schema.org/draft-04/schema#"
    type                 = "object"
    required             = ["customer_id"]
    additionalProperties = false
    properties = {
      customer_id = { type = "string", minLength = 1, maxLength = 64, pattern = "^[A-Za-z0-9_-]+$" }
      overrides   = { type = "object" }
    }
  })
}

resource "aws_api_gateway_request_validator" "body" {
  rest_api_id           = aws_api_gateway_rest_api.this.id
  name                  = "validate-body"
  validate_request_body = true
}

resource "aws_api_gateway_method" "predict" {
  rest_api_id          = aws_api_gateway_rest_api.this.id
  resource_id          = aws_api_gateway_resource.predict.id
  http_method          = "POST"
  authorization        = "NONE"
  api_key_required     = true
  request_validator_id = aws_api_gateway_request_validator.body.id
  request_models       = { "application/json" = aws_api_gateway_model.predict_request.name }
}

resource "aws_api_gateway_integration" "predict" {
  rest_api_id             = aws_api_gateway_rest_api.this.id
  resource_id             = aws_api_gateway_resource.predict.id
  http_method             = aws_api_gateway_method.predict.http_method
  type                    = "HTTP_PROXY"
  integration_http_method = "POST"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.this.id
  uri                     = "http://${aws_lb.this.dns_name}/v1/predict"
  timeout_milliseconds    = 3000
}

resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  triggers = {
    redeploy = sha1(jsonencode([
      aws_api_gateway_resource.predict, aws_api_gateway_method.predict, aws_api_gateway_integration.predict,
      aws_api_gateway_model.predict_request,
    ]))
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_cloudwatch_log_group" "access" {
  name              = "/aws/apigateway/${var.name}-api"
  retention_in_days = 30
  tags              = var.tags
}

# API Gateway needs an account-level role to write logs to CloudWatch.
data "aws_iam_policy_document" "apigw_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apigw_logs" {
  count              = var.manage_account_logging_role ? 1 : 0
  name               = "${var.name}-apigw-cloudwatch"
  assume_role_policy = data.aws_iam_policy_document.apigw_assume.json
}

resource "aws_iam_role_policy_attachment" "apigw_logs" {
  count      = var.manage_account_logging_role ? 1 : 0
  role       = aws_iam_role.apigw_logs[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

resource "aws_api_gateway_account" "this" {
  count               = var.manage_account_logging_role ? 1 : 0
  cloudwatch_role_arn = aws_iam_role.apigw_logs[0].arn
}

resource "aws_api_gateway_stage" "this" {
  rest_api_id   = aws_api_gateway_rest_api.this.id
  deployment_id = aws_api_gateway_deployment.this.id
  stage_name    = var.stage_name

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.access.arn
    format = jsonencode({
      requestId          = "$context.requestId", ip = "$context.identity.sourceIp", method = "$context.httpMethod",
      path               = "$context.resourcePath", status = "$context.status", latency = "$context.responseLatency",
      integrationLatency = "$context.integration.latency", apiKeyId = "$context.identity.apiKeyId"
    })
  }
  tags       = var.tags
  depends_on = [aws_api_gateway_account.this]
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  stage_name  = aws_api_gateway_stage.this.stage_name
  method_path = "*/*"
  settings {
    metrics_enabled        = true
    logging_level          = "ERROR"
    throttling_burst_limit = var.throttle_burst
    throttling_rate_limit  = var.throttle_rate
  }
}

resource "aws_api_gateway_usage_plan" "this" {
  name = "${var.name}-usage-plan"
  api_stages {
    api_id = aws_api_gateway_rest_api.this.id
    stage  = aws_api_gateway_stage.this.stage_name
  }
  throttle_settings {
    burst_limit = var.throttle_burst
    rate_limit  = var.throttle_rate
  }
  tags = var.tags
}

resource "aws_api_gateway_api_key" "clients" {
  for_each = toset(var.api_clients)
  name     = "${var.name}-${each.value}"
  tags     = var.tags
}

resource "aws_api_gateway_usage_plan_key" "clients" {
  for_each      = aws_api_gateway_api_key.clients
  key_id        = each.value.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.this.id
}
