output "vpc_id" {
  value = aws_vpc.main.id
}

output "raw_bucket" {
  value = aws_s3_bucket.raw.bucket
}

output "evidence_bucket" {
  value = aws_s3_bucket.evidence.bucket
}

output "intake_queue_url" {
  value = aws_sqs_queue.intake.url
}

output "idempotency_table" {
  value = aws_dynamodb_table.idempotency.name
}

output "results_cluster_endpoint" {
  value = aws_rds_cluster.results.endpoint
}

output "results_secret_arn" {
  description = "Secrets Manager secret holding the Aurora master credentials"
  value       = aws_rds_cluster.results.master_user_secret[0].secret_arn
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}

output "alerts_topic_arn" {
  value = aws_sns_topic.alerts.arn
}
