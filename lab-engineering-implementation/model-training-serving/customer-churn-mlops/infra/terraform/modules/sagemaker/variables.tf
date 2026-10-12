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

variable "features_yaml_path" {
  description = "Path to config/features.yaml - the single source of truth for the feature contract."
  type        = string
}

variable "feature_group_name" {
  type    = string
  default = "teleconnect-customer-features"
}

variable "model_package_group_name" {
  type    = string
  default = "Customer-Churn-Models"
}

variable "create_studio_domain" {
  type    = bool
  default = true
}

variable "studio_users" {
  type    = list(string)
  default = ["ml-engineer", "mlops-engineer", "solution-architect"]
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "tags" {
  type    = map(string)
  default = {}
}
