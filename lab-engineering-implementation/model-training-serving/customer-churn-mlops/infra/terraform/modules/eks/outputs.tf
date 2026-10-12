output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  value = module.eks.cluster_certificate_authority_data
}

output "node_security_group_id" {
  value = module.eks.node_security_group_id
}

output "churn_api_role_arn" {
  value = module.churn_api_irsa.iam_role_arn
}

output "app_namespace" {
  value = kubernetes_namespace.churn.metadata[0].name
}
