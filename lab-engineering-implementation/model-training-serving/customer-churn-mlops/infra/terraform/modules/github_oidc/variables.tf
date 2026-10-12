variable "project" {
  type = string
}

variable "github_repository" {
  description = "owner/repo"
  type        = string
}

variable "create_provider" {
  description = "false if the account already has the GitHub OIDC provider."
  type        = bool
  default     = true
}

variable "sagemaker_role_arn" {
  type = string
}

variable "bucket_arn" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "ecr_repository_arns" {
  type = list(string)
}

variable "eks_cluster_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
