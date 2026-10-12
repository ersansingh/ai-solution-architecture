output "bucket_name" {
  value = module.data_lake.bucket_name
}

output "sagemaker_execution_role_arn" {
  value = module.sagemaker.execution_role_arn
}

output "feature_group_name" {
  value = module.sagemaker.feature_group_name
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "api_invoke_url" {
  value = module.api.invoke_url
}

output "api_key_ids" {
  description = "aws apigateway get-api-key --api-key <id> --include-value"
  value       = module.api.api_key_ids
}

output "deploy_state_machine_arn" {
  value = module.deploy.state_machine_arn
}

output "github_deploy_role_arn" {
  value = try(module.github_oidc[0].role_arn, null)
}

# Consumed by CI: `terraform output -raw churn_api_helm_values > values-aws.yaml`
output "churn_api_helm_values" {
  value = yamlencode({
    serviceAccount     = { annotations = { "eks.amazonaws.com/role-arn" = module.eks.churn_api_role_arn } }
    targetGroupBinding = { enabled = true, targetGroupArn = module.api.target_group_arn }
    env = {
      AWS_REGION               = var.region
      FEATURE_BACKEND          = "featurestore"
      FEATURE_GROUP_NAME       = module.sagemaker.feature_group_name
      MODEL_BACKEND            = "sagemaker"
      SERVING_CONFIG_PARAMETER = module.deploy.serving_config_parameters["prod"]
      METRICS_ENABLED          = "true"
    }
  })
}
