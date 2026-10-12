variable "project" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "pipeline_name" {
  type    = string
  default = "CustomerChurnPipeline"
}

variable "model_package_group_name" {
  type    = string
  default = "Customer-Churn-Models"
}

variable "retrain_target" {
  description = "sagemaker_pipeline (AWS) or sqs (LocalStack: records trigger events for the integration tests)."
  type        = string
  default     = "sagemaker_pipeline"
  validation {
    condition     = contains(["sagemaker_pipeline", "sqs"], var.retrain_target)
    error_message = "retrain_target must be sagemaker_pipeline or sqs."
  }
}

variable "retrain_queue_arn" {
  type    = string
  default = null
}

variable "deploy_state_machine_arn" {
  type    = string
  default = null
}

variable "sns_topic_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
