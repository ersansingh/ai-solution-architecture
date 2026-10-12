variable "name" {
  type = string
}

variable "cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "single_nat_gateway" {
  description = "One NAT gateway (lab, cheaper) instead of one per AZ (production)."
  type        = bool
  default     = true
}

variable "interface_endpoints" {
  type = list(string)
  default = [
    "sagemaker.runtime", "sagemaker.featurestore-runtime", "sagemaker.api", "sts", "ssm",
    "monitoring", "logs", "ecr.api", "ecr.dkr",
  ]
}

variable "tags" {
  type    = map(string)
  default = {}
}
