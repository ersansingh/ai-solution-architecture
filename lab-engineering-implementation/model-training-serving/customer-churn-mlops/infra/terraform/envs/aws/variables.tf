variable "region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "lab"
}

variable "owner" {
  type    = string
  default = "ml-platform"
}

variable "cost_center" {
  type    = string
  default = "retention-analytics"
}

variable "bucket_name" {
  description = "teleconnect-churn-<name>-lab (globally unique)"
  type        = string
}

variable "force_destroy" {
  description = "Lab teardown: allow destroying the non-empty bucket and ECR repositories."
  type        = bool
  default     = false
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "single_nat_gateway" {
  type    = bool
  default = true
}

variable "cluster_name" {
  type    = string
  default = "teleconnect-churn"
}

variable "cluster_version" {
  type    = string
  default = "1.31"
}

variable "node_instance_types" {
  type    = list(string)
  default = ["m5.large"]
}

variable "eks_public_access_cidrs" {
  description = "CIDRs allowed to reach the EKS API (restrict to your office / runner ranges)."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "create_studio_domain" {
  type    = bool
  default = true
}

variable "endpoint_instance_type" {
  type    = string
  default = "ml.c5.large"
}

variable "api_throttle_rate" {
  type    = number
  default = 100
}

variable "api_throttle_burst" {
  type    = number
  default = 200
}

variable "manage_apigw_account_role" {
  type    = bool
  default = true
}

variable "alert_emails" {
  type    = list(string)
  default = []
}

variable "monthly_budget_usd" {
  type    = number
  default = 500
}

variable "github_repository" {
  description = "owner/repo for GitHub Actions OIDC; empty disables the CI/CD role."
  type        = string
  default     = ""
}

variable "create_github_oidc_provider" {
  type    = bool
  default = true
}
