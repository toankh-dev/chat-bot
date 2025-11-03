# API Gateway Module Variables

variable "name_prefix" {
  description = "Prefix for all API Gateway resource names"
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
# API Gateway Configuration
# ============================================================================

variable "api_description" {
  description = "Description of the API Gateway"
  type        = string
  default     = "KASS Chatbot REST API"
}

variable "stage_name" {
  description = "Stage name for API Gateway deployment"
  type        = string
  default     = "v1"
}

variable "endpoint_type" {
  description = "Endpoint type for API Gateway (REGIONAL, EDGE, PRIVATE)"
  type        = string
  default     = "REGIONAL"
  validation {
    condition     = contains(["REGIONAL", "EDGE", "PRIVATE"], var.endpoint_type)
    error_message = "Endpoint type must be REGIONAL, EDGE, or PRIVATE"
  }
}

variable "minimum_compression_size" {
  description = "Minimum response size to compress for the REST API (bytes, -1 to disable)"
  type        = number
  default     = 1024
}

# ============================================================================
# Lambda Integration Configuration (New Dynamic Structure)
# ============================================================================

variable "lambda_integrations" {
  description = "Map of route patterns to Lambda integration configurations"
  type = map(object({
    lambda_arn            = string
    lambda_invoke_arn     = string
    timeout_milliseconds  = optional(number, 29000)
    authorization         = optional(string, "NONE")
    api_key_required      = optional(bool, false)
  }))
  default = {}
}

# ============================================================================
# CORS Configuration
# ============================================================================

variable "cors_configuration" {
  description = "CORS configuration for API Gateway"
  type = object({
    allow_origins = list(string)
    allow_methods = list(string)
    allow_headers = list(string)
    max_age       = number
  })
  default = {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Api-Key"]
    max_age       = 300
  }
}

# ============================================================================
# Authentication & Authorization
# ============================================================================

variable "enable_api_key_auth" {
  description = "Enable API key authentication"
  type        = bool
  default     = true
}

variable "enable_cognito_auth" {
  description = "Enable Cognito authentication"
  type        = bool
  default     = false
}

variable "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool for authentication"
  type        = string
  default     = ""
}

# ============================================================================
# Usage Plan Configuration
# ============================================================================

variable "usage_plan_rate_limit" {
  description = "Usage plan rate limit (requests per second)"
  type        = number
  default     = 100
}

variable "usage_plan_burst_limit" {
  description = "Usage plan burst limit"
  type        = number
  default     = 200
}

variable "usage_plan_quota_limit" {
  description = "Usage plan quota limit (total requests per period)"
  type        = number
  default     = 100000
}

variable "usage_plan_quota_period" {
  description = "Usage plan quota period (DAY, WEEK, MONTH)"
  type        = string
  default     = "MONTH"
  validation {
    condition     = contains(["DAY", "WEEK", "MONTH"], var.usage_plan_quota_period)
    error_message = "Quota period must be DAY, WEEK, or MONTH"
  }
}

# ============================================================================
# Throttling Configuration
# ============================================================================

variable "throttle_rate_limit" {
  description = "Throttle rate limit for API methods (requests per second)"
  type        = number
  default     = 100
}

variable "throttle_burst_limit" {
  description = "Throttle burst limit for API methods"
  type        = number
  default     = 200
}

# ============================================================================
# Caching Configuration
# ============================================================================

variable "enable_cache" {
  description = "Enable API Gateway caching"
  type        = bool
  default     = false
}

variable "cache_size" {
  description = "Cache size in GB (0.5, 1.6, 6.1, 13.5, 28.4, 58.2, 118, 237)"
  type        = string
  default     = "0.5"
  validation {
    condition     = contains(["0.5", "1.6", "6.1", "13.5", "28.4", "58.2", "118", "237"], var.cache_size)
    error_message = "Cache size must be one of: 0.5, 1.6, 6.1, 13.5, 28.4, 58.2, 118, 237"
  }
}

variable "cache_ttl_seconds" {
  description = "Cache TTL in seconds"
  type        = number
  default     = 300
}

# ============================================================================
# Logging Configuration
# ============================================================================

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7
}

variable "logging_level" {
  description = "Logging level for API Gateway (OFF, ERROR, INFO)"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["OFF", "ERROR", "INFO"], var.logging_level)
    error_message = "Logging level must be OFF, ERROR, or INFO"
  }
}

variable "enable_data_trace" {
  description = "Enable full request/response data logging (only for troubleshooting)"
  type        = bool
  default     = false
}

variable "enable_metrics" {
  description = "Enable detailed CloudWatch metrics"
  type        = bool
  default     = true
}

variable "enable_access_logging" {
  description = "Enable access logging for API Gateway"
  type        = bool
  default     = true
}

variable "enable_execution_logging" {
  description = "Enable execution logging for API Gateway"
  type        = bool
  default     = true
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "enable_xray" {
  description = "Enable X-Ray tracing for API Gateway"
  type        = bool
  default     = true
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for API Gateway"
  type        = bool
  default     = true
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms"
  type        = string
  default     = ""
}

variable "error_4xx_threshold" {
  description = "Threshold for 4XX error alarm"
  type        = number
  default     = 50
}

variable "error_5xx_threshold" {
  description = "Threshold for 5XX error alarm"
  type        = number
  default     = 10
}

variable "latency_threshold_ms" {
  description = "Latency threshold in milliseconds for alarm"
  type        = number
  default     = 5000
}
