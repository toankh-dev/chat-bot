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

# ============================================================================
# Lambda Function ARNs
# ============================================================================

variable "orchestrator_lambda_arn" {
  description = "ARN of the orchestrator Lambda function"
  type        = string
  default     = ""
}

variable "vector_search_lambda_arn" {
  description = "ARN of the vector search Lambda function"
  type        = string
  default     = ""
}

variable "document_processor_lambda_arn" {
  description = "ARN of the document processor Lambda function"
  type        = string
}

variable "data_fetcher_lambda_arn" {
  description = "ARN of the data fetcher Lambda function"
  type        = string
  default     = ""
}

variable "discord_handler_lambda_arn" {
  description = "ARN of the Discord handler Lambda function"
  type        = string
  default     = ""
}

variable "report_tool_lambda_arn" {
  description = "ARN of the report generation Lambda function"
  type        = string
  default     = ""
}

# ============================================================================
# S3 Configuration
# ============================================================================

variable "documents_bucket_name" {
  description = "Name of the S3 bucket for documents"
  type        = string
}

# ============================================================================
# Feature Flags
# ============================================================================

variable "enable_scheduled_fetch" {
  description = "Enable scheduled data fetching"
  type        = bool
  default     = true
}

variable "enable_discord_fetch" {
  description = "Enable scheduled Discord message fetching"
  type        = bool
  default     = false
}

variable "enable_report_generation" {
  description = "Enable async report generation"
  type        = bool
  default     = true
}

variable "enable_cache_warming" {
  description = "Enable Lambda cache warming (reduces cold starts)"
  type        = bool
  default     = false
}

# ============================================================================
# Schedule Configuration
# ============================================================================

variable "fetch_schedule" {
  description = "Schedule expression for data fetching (e.g., 'rate(1 day)' or 'cron(0 0 * * ? *)')"
  type        = string
  default     = "rate(1 day)"
}

variable "discord_fetch_schedule" {
  description = "Schedule expression for Discord message fetching"
  type        = string
  default     = "rate(1 hour)"
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
