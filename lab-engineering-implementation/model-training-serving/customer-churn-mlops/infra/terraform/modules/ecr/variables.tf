variable "repositories" {
  type    = list(string)
  default = ["churn-api", "churn-lightgbm"]
}

variable "kms_key_arn" {
  type = string
}

variable "force_delete" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
