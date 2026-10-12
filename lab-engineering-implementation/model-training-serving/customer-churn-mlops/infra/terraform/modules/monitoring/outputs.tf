output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "rollback_alarm_names" {
  value = [aws_cloudwatch_metric_alarm.rollback_5xx.alarm_name, aws_cloudwatch_metric_alarm.rollback_latency.alarm_name]
}
