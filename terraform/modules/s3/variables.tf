# ============================================================================
# S3 Module Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for bucket names"
  type        = string
}

variable "account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "buckets" {
  description = "Map of bucket configurations"
  type = map(object({
    versioning_enabled = bool
    lifecycle_rules = list(object({
      id      = string
      enabled = bool
      prefix  = optional(string)
      transitions = optional(list(object({
        days          = number
        storage_class = string
      })))
      expiration = optional(object({
        days = number
      }))
    }))
  }))
}

variable "enable_event_notifications" {
  description = "Enable S3 event notifications to Lambda"
  type        = bool
  default     = false
}

variable "lambda_processor_arn" {
  description = "ARN of Lambda function to process S3 events"
  type        = string
  default     = null
}

variable "enable_cors" {
  description = "Enable CORS configuration for documents bucket"
  type        = bool
  default     = false
}

variable "cors_allowed_origins" {
  description = "Allowed origins for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "enable_metrics" {
  description = "Enable CloudWatch metrics for buckets"
  type        = bool
  default     = false
}

variable "enable_intelligent_tiering" {
  description = "Enable S3 Intelligent-Tiering"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
