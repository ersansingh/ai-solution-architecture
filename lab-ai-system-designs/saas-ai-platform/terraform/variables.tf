variable "primary_region" {
  description = "Primary AWS deployment region"
  type        = "string"
  default     = "us-east-1"
}

variable "secondary_regions" {
  description = "List of secondary AWS regional hubs"
  type        = list(string)
  default     = ["eu-west-1", "ap-southeast-1", "ap-northeast-1", "us-west-2"]
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the regional AI Hub VPC"
  type        = string
  default     = "10.100.0.0/16"
}
