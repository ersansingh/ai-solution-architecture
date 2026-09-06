output "vpc_id" {
  description = "The ID of the primary AI Hub VPC"
  value       = module.vpc.vpc_id
}

output "eks_cluster_name" {
  description = "The name of the primary EKS AI cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "The API endpoint of the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "opensearch_collection_endpoint" {
  description = "Endpoint for the OpenSearch Serverless Vector Collection"
  value       = aws_opensearchserverless_collection.vector_db.collection_endpoint
}

output "semantic_cache_endpoint" {
  description = "Primary endpoint address for ElastiCache Redis Semantic Cache"
  value       = aws_elasticache_replication_group.semantic_cache.primary_endpoint_address
}

output "aurora_global_cluster_id" {
  description = "Identifier for Aurora PostgreSQL Global Database"
  value       = aws_rds_global_cluster.aurora_global.id
}
