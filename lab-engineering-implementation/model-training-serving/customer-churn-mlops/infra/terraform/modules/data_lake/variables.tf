variable "project" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "force_destroy" {
  description = "Allow terraform destroy to delete a non-empty bucket (lab teardown)."
  type        = bool
  default     = false
}

variable "enforce_tls" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
