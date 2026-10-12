output "execution_role_arn" {
  value = aws_iam_role.execution.arn
}

output "feature_group_arn" {
  value = aws_sagemaker_feature_group.customers.arn
}

output "feature_group_name" {
  value = aws_sagemaker_feature_group.customers.feature_group_name
}

output "model_package_group_name" {
  value = aws_sagemaker_model_package_group.churn.model_package_group_name
}

output "model_package_group_arn" {
  value = aws_sagemaker_model_package_group.churn.arn
}

output "athena_workgroup" {
  value = aws_athena_workgroup.churn.name
}

output "studio_domain_id" {
  value = try(aws_sagemaker_domain.studio[0].id, null)
}
