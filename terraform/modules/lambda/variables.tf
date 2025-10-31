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

variable "lambda_execution_role_arn" {
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

variable "lambda_functions" {
  description = "Map of Lambda functions to create"
  type = map(object({
    description                    = string
    handler                        = string
    zip_path                       = string
    timeout                        = optional(number)
    memory_size                    = optional(number)
    environment_variables          = optional(map(string))
    use_langchain_layer            = optional(bool, false)
    use_document_layer             = optional(bool, false)
    additional_layers              = optional(list(string), [])
    reserved_concurrent_executions = optional(number)
    dead_letter_queue_arn          = optional(string)
    ephemeral_storage_size         = optional(number, 512)
    allow_api_gateway              = optional(bool, false)
    allow_eventbridge              = optional(bool, false)
    allow_s3                       = optional(bool, false)
    enable_function_url            = optional(bool, false)
    function_url_auth_type         = optional(string, "AWS_IAM")
    enable_cors                    = optional(bool, false)
    cors_allow_credentials         = optional(bool, false)
    cors_allow_origins             = optional(list(string), ["*"])
    cors_allow_methods             = optional(list(string), ["GET", "POST"])
    cors_allow_headers             = optional(list(string), ["*"])
    cors_max_age                   = optional(number, 86400)
    error_threshold                = optional(number, 10)
    throttle_threshold             = optional(number, 5)
  }))
  default = {}
}

variable "common_environment_variables" {
  description = "Common environment variables for all Lambda functions"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Lambda Layers Configuration
# ============================================================================

variable "create_common_layer" {
  description = "Create the common utilities Lambda layer"
  type        = bool
  default     = true
}

variable "common_layer_zip_path" {
  description = "Path to the common utilities layer zip file"
  type        = string
  default     = ""
}

variable "create_langchain_layer" {
  description = "Create the LangChain Lambda layer"
  type        = bool
  default     = true
}

variable "langchain_layer_zip_path" {
  description = "Path to the LangChain layer zip file"
  type        = string
  default     = ""
}

variable "create_document_layer" {
  description = "Create the document processing Lambda layer"
  type        = bool
  default     = true
}

variable "document_layer_zip_path" {
  description = "Path to the document processing layer zip file"
  type        = string
  default     = ""
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
