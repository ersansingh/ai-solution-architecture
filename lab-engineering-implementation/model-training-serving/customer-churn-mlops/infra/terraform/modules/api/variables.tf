variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "target_port" {
  type    = number
  default = 8080
}

variable "stage_name" {
  type    = string
  default = "prod"
}

variable "throttle_rate" {
  description = "Steady-state requests/second (2x the OD-3 peak of 50 RPS)."
  type        = number
  default     = 100
}

variable "throttle_burst" {
  type    = number
  default = 200
}

variable "api_clients" {
  description = "One API key per consuming application."
  type        = list(string)
  default     = ["support-desk", "load-test"]
}

variable "manage_account_logging_role" {
  description = "Set false if the account already has an API Gateway CloudWatch role configured."
  type        = bool
  default     = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
