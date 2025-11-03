# EventBridge Module Variables

variable "name_prefix" {
  description = "Prefix for all EventBridge resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# ============================================================================
# EventBridge Configuration
# ============================================================================

variable "create_custom_event_bus" {
  description = "Create a custom event bus (if false, uses default event bus)"
  type        = bool
  default     = false
}

variable "custom_event_bus_name" {
  description = "Name of the custom event bus (if create_custom_event_bus is true)"
  type        = string
  default     = ""
}

# ============================================================================
# Dynamic Rules Configuration (New Structure)
# ============================================================================

variable "rules" {
  description = "Map of EventBridge rules configurations"
  type = map(object({
    description          = optional(string, "")
    event_pattern        = optional(string, null)
    schedule_expression  = optional(string, null)
    enabled              = optional(bool, true)
    targets = list(object({
      arn              = string
      input            = optional(string, null)
      input_path       = optional(string, null)
      role_arn         = optional(string, null)
      dead_letter_arn  = optional(string, null)
      retry_policy = optional(object({
        maximum_event_age       = optional(number, 3600)
        maximum_retry_attempts  = optional(number, 2)
      }), null)
    }))
  }))
  default = {}
}

# ============================================================================
# Lambda Function ARNs Map (for backward compatibility and permissions)
# ============================================================================

variable "lambda_function_arns" {
  description = "Map of Lambda function ARNs for creating permissions"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Dead Letter Queue Configuration
# ============================================================================

variable "create_dlq" {
  description = "Create a Dead Letter Queue for failed events"
  type        = bool
  default     = true
}

variable "dlq_arn" {
  description = "ARN of an existing DLQ (if create_dlq is false)"
  type        = string
  default     = ""
}

variable "dlq_message_retention_seconds" {
  description = "Message retention period for DLQ in seconds"
  type        = number
  default     = 1209600  # 14 days
}

# ============================================================================
# Logging Configuration
# ============================================================================

variable "enable_eventbridge_logging" {
  description = "Enable logging for EventBridge"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for EventBridge"
  type        = bool
  default     = true
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms"
  type        = string
  default     = ""
}

variable "failed_invocations_threshold" {
  description = "Threshold for failed invocations alarm"
  type        = number
  default     = 10
}

variable "throttled_rules_threshold" {
  description = "Threshold for throttled rules alarm"
  type        = number
  default     = 5
}

# ============================================================================
# IAM Role Configuration
# ============================================================================

variable "create_event_bus_role" {
  description = "Create an IAM role for EventBridge to invoke targets"
  type        = bool
  default     = true
}

variable "event_bus_role_arn" {
  description = "ARN of an existing IAM role for EventBridge (if create_event_bus_role is false)"
  type        = string
  default     = ""
}
