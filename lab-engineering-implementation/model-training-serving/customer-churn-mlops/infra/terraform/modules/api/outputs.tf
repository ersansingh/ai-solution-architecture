output "invoke_url" {
  value = "${aws_api_gateway_stage.this.invoke_url}/v1/predict"
}

output "rest_api_name" {
  value = aws_api_gateway_rest_api.this.name
}

output "stage_name" {
  value = aws_api_gateway_stage.this.stage_name
}

output "api_key_ids" {
  value = { for k, v in aws_api_gateway_api_key.clients : k => v.id }
}

output "target_group_arn" {
  value = aws_lb_target_group.this.arn
}

output "nlb_security_group_id" {
  value = aws_security_group.nlb.id
}
