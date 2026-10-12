output "manifest_rule_name" {
  value = aws_cloudwatch_event_rule.manifest.name
}

output "monthly_rule_name" {
  value = aws_cloudwatch_event_rule.monthly.name
}
