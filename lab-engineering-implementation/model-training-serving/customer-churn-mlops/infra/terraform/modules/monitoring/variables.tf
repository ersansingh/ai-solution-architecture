variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "features_yaml_path" {
  type = string
}

variable "topic_name" {
  type    = string
  default = "customer-churn-alerts"
}

variable "sns_kms_key_id" {
  type    = string
  default = null
}

variable "alert_emails" {
  type    = list(string)
  default = []
}

variable "endpoint_name" {
  type    = string
  default = "customer-churn-prod"
}

variable "variant_name" {
  type    = string
  default = "AllTraffic"
}

variable "api_name" {
  type    = string
  default = ""
}

variable "api_stage" {
  type    = string
  default = "prod"
}

variable "create_api_alarms" {
  type    = bool
  default = true
}

variable "app_metrics_namespace" {
  type    = string
  default = "TeleConnect/Churn"
}

variable "cpu_threshold" {
  description = "Endpoint CPUUtilization is the sum over vCPUs; 160 = 80% of a 2-vCPU ml.c5.large."
  type        = number
  default     = 160
}

variable "drift_features" {
  description = "Numeric features (top SHAP) with drift alarms."
  type        = list(string)
  default     = ["satisfaction_score", "complaint_count", "tenure_months", "avg_days_past_due", "usage_growth_rate", "monthly_charges"]
}

variable "drift_threshold" {
  type    = number
  default = 0.2
}

variable "training_churn_rate" {
  type    = number
  default = 0.18
}

variable "create_dashboard" {
  type    = bool
  default = true
}

variable "monthly_budget_usd" {
  description = "0 disables the AWS Budget."
  type        = number
  default     = 500
}

variable "tags" {
  type    = map(string)
  default = {}
}
