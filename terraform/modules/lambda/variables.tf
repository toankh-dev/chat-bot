# Lambda Module Variables

variable "name_prefix" {
  description = "Prefix for all Lambda resource names"
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
# Lambda Configuration
# ============================================================================

variable "python_runtime" {
  description = "Python runtime version for Lambda functions"
  type        = string
  default     = "python3.11"
}

variable "execution_role_arn" {
  description = "ARN of the IAM role for Lambda execution"
  type        = string
}

variable "default_timeout" {
  description = "Default timeout for Lambda functions in seconds"
  type        = number
  default     = 300
}

variable "default_memory_size" {
  description = "Default memory size for Lambda functions in MB"
  type        = number
  default     = 1024
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7
}

# ============================================================================
# Lambda Functions Configuration
# ============================================================================
variable "functions" {
  description = "Simplified map of Lambda functions configuration"
  type = map(object({
    handler     = string
    memory_size = optional(number, 1024)
    timeout     = optional(number, 300)
    runtime     = optional(string, "python3.11")
  }))
  default = {}
}

variable "environment_variables" {
  description = "Environment variables shared across all Lambda functions"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Lambda Layers Configuration
# ============================================================================
variable "layers" {
  description = "Simplified list of Lambda layers configuration"
  type = list(object({
    name                 = string
    description          = optional(string, "")
    compatible_runtimes  = optional(list(string), ["python3.11"])
  }))
  default = []
}

# ============================================================================
# VPC Configuration
# ============================================================================

variable "enable_vpc_config" {
  description = "Enable VPC configuration for Lambda functions"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC ID for Lambda functions (if enable_vpc_config is true)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "List of subnet IDs for Lambda functions (if enable_vpc_config is true)"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "List of security group IDs for Lambda functions (if enable_vpc_config is true)"
  type        = list(string)
  default     = []
}

# ============================================================================
# Integration Configuration
# ============================================================================

variable "api_gateway_execution_arn" {
  description = "Execution ARN of the API Gateway (for Lambda permissions)"
  type        = string
  default     = ""
}

variable "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule (for Lambda permissions)"
  type        = string
  default     = ""
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket (for Lambda permissions)"
  type        = string
  default     = ""
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "enable_xray" {
  description = "Enable X-Ray tracing for Lambda functions"
  type        = bool
  default     = true
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for Lambda functions"
  type        = bool
  default     = true
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms"
  type        = string
  default     = ""
}
