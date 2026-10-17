variable "project" {
  description = "Resource name prefix"
  type        = string
  default     = "invoice-recon"
}

variable "environment" {
  description = "dev | staging | prod"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "Primary AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "azs" {
  description = "Two availability zones"
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b"]
}

variable "container_image" {
  description = "Reconciler service image (ECR URI with tag)"
  type        = string
  default     = "public.ecr.aws/docker/library/busybox:latest" # placeholder until the CI pipeline pushes a real image
}

variable "evidence_retention_days" {
  description = "S3 Object Lock retention for evidence bundles. PLACEHOLDER: set from the approved audit-retention policy (BRD section 15)."
  type        = number
  default     = 365
}

variable "monthly_budget_usd" {
  description = "Monthly cost budget for alerts. PLACEHOLDER: agree with the business."
  type        = number
  default     = 2000
}

variable "alert_email" {
  description = "On-call / FinOps notification address"
  type        = string
  default     = "ops@example.com"
}
