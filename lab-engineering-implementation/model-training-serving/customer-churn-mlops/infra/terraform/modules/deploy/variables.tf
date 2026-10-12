variable "project" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "bucket_arn" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "endpoint_role_arn" {
  type = string
}

variable "sns_topic_arn" {
  type = string
}

variable "rollback_alarm_names" {
  type = list(string)
}

variable "lambda_source_dir" {
  type = string
}

variable "state_machine_definition_path" {
  type = string
}

variable "staging_endpoint_name" {
  type    = string
  default = "customer-churn-staging"
}

variable "prod_endpoint_name" {
  type    = string
  default = "customer-churn-prod"
}

variable "endpoint_instance_type" {
  type    = string
  default = "ml.c5.large"
}

variable "prod_min_instances" {
  description = ">= 2 for the 99.9% availability target (plan G11)."
  type        = number
  default     = 2
}

variable "prod_max_instances" {
  type    = number
  default = 6
}

variable "target_invocations_per_instance" {
  description = "Auto-scaling target; replace with the value measured in the M6 load test."
  type        = number
  default     = 600
}

variable "prod_capture_pct" {
  type    = number
  default = 20
}

variable "tags" {
  type    = map(string)
  default = {}
}
