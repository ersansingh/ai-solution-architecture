variable "cluster_name" {
  type = string
}

variable "cluster_version" {
  type    = string
  default = "1.31"
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "endpoint_public_access" {
  description = "Public API endpoint for the lab (kubectl from a laptop / GitHub runners). Disable in production."
  type        = bool
  default     = true
}

variable "endpoint_public_access_cidrs" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}

variable "node_instance_types" {
  type    = list(string)
  default = ["m5.large"]
}

variable "node_min" {
  type    = number
  default = 2
}

variable "node_max" {
  type    = number
  default = 6
}

variable "node_desired" {
  type    = number
  default = 3
}

variable "admin_role_arns" {
  description = "Extra IAM roles (e.g. the GitHub Actions deploy role) granted cluster admin."
  type        = map(string)
  default     = {}
}

variable "app_namespace" {
  type    = string
  default = "churn"
}

variable "feature_group_arn" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "serving_config_parameter_prefix" {
  type    = string
  default = "/teleconnect-churn/"
}

variable "metrics_namespace" {
  type    = string
  default = "TeleConnect/Churn"
}

variable "lb_controller_chart_version" {
  type    = string
  default = "1.10.1"
}

variable "metrics_server_chart_version" {
  type    = string
  default = "3.12.2"
}

variable "tags" {
  type    = map(string)
  default = {}
}
