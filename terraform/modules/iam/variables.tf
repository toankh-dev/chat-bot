# IAM Module Variables

variable "name_prefix" {
  description = "Prefix for all IAM resource names"
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
# Service-Specific Variables
# ============================================================================

variable "opensearch_collection_arn" {
  description = "ARN of the OpenSearch Serverless collection"
  type        = string
  default     = ""
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs that Lambda functions need access to"
  type        = list(string)
  default     = []
}

variable "s3_bucket_arns" {
  description = "List of S3 bucket ARNs that Lambda functions need access to"
  type        = list(string)
  default     = []
}

# ============================================================================
# Feature Flags
# ============================================================================

variable "enable_vpc_access" {
  description = "Enable VPC access for Lambda functions"
  type        = bool
  default     = true
}

variable "enable_xray" {
  description = "Enable X-Ray tracing for Lambda functions"
  type        = bool
  default     = true
}

variable "enable_secrets_manager" {
  description = "Enable Secrets Manager access for Lambda functions"
  type        = bool
  default     = true
}
