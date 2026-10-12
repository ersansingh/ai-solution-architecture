output "state_machine_arn" {
  value = aws_sfn_state_machine.deploy.arn
}

output "serving_config_parameters" {
  value = { for k, p in aws_ssm_parameter.serving_config : k => p.name }
}
