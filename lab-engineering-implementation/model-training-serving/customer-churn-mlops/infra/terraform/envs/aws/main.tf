locals {
  project       = "teleconnect-churn"
  repo_root     = abspath("${path.module}/../../../..")
  features_yaml = "${local.repo_root}/config/features.yaml"
  tags = {
    project       = local.project
    env           = var.environment
    owner         = var.owner
    "cost-center" = var.cost_center
  }
}

module "network" {
  source             = "../../modules/network"
  name               = local.project
  cidr               = var.vpc_cidr
  single_nat_gateway = var.single_nat_gateway
  tags               = local.tags
}

module "data_lake" {
  source        = "../../modules/data_lake"
  project       = local.project
  bucket_name   = var.bucket_name
  force_destroy = var.force_destroy
  tags          = local.tags
}

module "ecr" {
  source       = "../../modules/ecr"
  kms_key_arn  = module.data_lake.kms_key_arn
  force_delete = var.force_destroy
  tags         = local.tags
}

module "sagemaker" {
  source               = "../../modules/sagemaker"
  project              = local.project
  bucket_name          = module.data_lake.bucket_name
  bucket_arn           = module.data_lake.bucket_arn
  kms_key_arn          = module.data_lake.kms_key_arn
  features_yaml_path   = local.features_yaml
  create_studio_domain = var.create_studio_domain
  vpc_id               = module.network.vpc_id
  private_subnet_ids   = module.network.private_subnet_ids
  tags                 = local.tags
}

module "api" {
  source                      = "../../modules/api"
  name                        = local.project
  vpc_id                      = module.network.vpc_id
  vpc_cidr                    = module.network.vpc_cidr
  private_subnet_ids          = module.network.private_subnet_ids
  throttle_rate               = var.api_throttle_rate
  throttle_burst              = var.api_throttle_burst
  manage_account_logging_role = var.manage_apigw_account_role
  tags                        = local.tags
}

module "github_oidc" {
  source              = "../../modules/github_oidc"
  count               = var.github_repository == "" ? 0 : 1
  project             = local.project
  github_repository   = var.github_repository
  create_provider     = var.create_github_oidc_provider
  sagemaker_role_arn  = module.sagemaker.execution_role_arn
  bucket_arn          = module.data_lake.bucket_arn
  kms_key_arn         = module.data_lake.kms_key_arn
  ecr_repository_arns = values(module.ecr.repository_arns)
  eks_cluster_name    = var.cluster_name
  tags                = local.tags
}

module "eks" {
  source                       = "../../modules/eks"
  cluster_name                 = var.cluster_name
  cluster_version              = var.cluster_version
  vpc_id                       = module.network.vpc_id
  private_subnet_ids           = module.network.private_subnet_ids
  feature_group_arn            = module.sagemaker.feature_group_arn
  kms_key_arn                  = module.data_lake.kms_key_arn
  node_instance_types          = var.node_instance_types
  endpoint_public_access_cidrs = var.eks_public_access_cidrs
  admin_role_arns              = var.github_repository == "" ? {} : { github = module.github_oidc[0].role_arn }
  tags                         = local.tags
}

# NLB (target type ip) -> churn-api pods, which use the node security group (VPC CNI).
resource "aws_security_group_rule" "nlb_to_pods" {
  type                     = "ingress"
  description              = "churn-api from the internal NLB"
  security_group_id        = module.eks.node_security_group_id
  source_security_group_id = module.api.nlb_security_group_id
  protocol                 = "tcp"
  from_port                = 8080
  to_port                  = 8080
}

module "monitoring" {
  source             = "../../modules/monitoring"
  project            = local.project
  region             = var.region
  features_yaml_path = local.features_yaml
  alert_emails       = var.alert_emails
  api_name           = module.api.rest_api_name
  api_stage          = module.api.stage_name
  monthly_budget_usd = var.monthly_budget_usd
  tags               = local.tags
}

module "deploy" {
  source                        = "../../modules/deploy"
  project                       = local.project
  bucket_name                   = module.data_lake.bucket_name
  bucket_arn                    = module.data_lake.bucket_arn
  kms_key_arn                   = module.data_lake.kms_key_arn
  endpoint_role_arn             = module.sagemaker.execution_role_arn
  sns_topic_arn                 = module.monitoring.sns_topic_arn
  rollback_alarm_names          = module.monitoring.rollback_alarm_names
  lambda_source_dir             = "${local.repo_root}/deployment/lambdas"
  state_machine_definition_path = "${local.repo_root}/deployment/stepfunctions/deploy.asl.json"
  endpoint_instance_type        = var.endpoint_instance_type
  tags                          = local.tags
}

module "events" {
  source                   = "../../modules/events"
  project                  = local.project
  bucket_name              = module.data_lake.bucket_name
  model_package_group_name = module.sagemaker.model_package_group_name
  deploy_state_machine_arn = module.deploy.state_machine_arn
  sns_topic_arn            = module.monitoring.sns_topic_arn
  tags                     = local.tags
}
