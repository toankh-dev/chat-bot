# OpenSearch Serverless Module Variables

variable "name_prefix" {
  description = "Prefix for all OpenSearch resource names"
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
# Collection Configuration
# ============================================================================

variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,31}$", var.collection_name))
    error_message = "Collection name must be between 3-32 characters, start with lowercase letter, and contain only lowercase letters, numbers, and hyphens"
  }
}

variable "collection_description" {
  description = "Description of the OpenSearch Serverless collection"
  type        = string
  default     = "Vector search collection for KASS Chatbot knowledge base"
}

# ============================================================================
# Network Configuration
# ============================================================================

variable "allow_public_access" {
  description = "Allow public access to the OpenSearch collection"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC ID for VPC endpoint (if create_vpc_endpoint is true)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "List of subnet IDs for VPC endpoint (if create_vpc_endpoint is true)"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "List of security group IDs for VPC endpoint (if create_vpc_endpoint is true)"
  type        = list(string)
  default     = []
}

variable "vpc_endpoint_ids" {
  description = "List of VPC endpoint IDs that can access the collection"
  type        = list(string)
  default     = null
}

variable "create_vpc_endpoint" {
  description = "Create a VPC endpoint for private access to OpenSearch Serverless"
  type        = bool
  default     = false
}

# ============================================================================
# Access Configuration
# ============================================================================

variable "lambda_execution_role_arns" {
  description = "List of Lambda execution role ARNs that need access to OpenSearch"
  type        = list(string)
  default     = []
}

variable "admin_user_arns" {
  description = "List of IAM user/role ARNs that should have admin access to OpenSearch"
  type        = list(string)
  default     = []
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for OpenSearch collection"
  type        = bool
  default     = true
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms"
  type        = string
  default     = ""
}

variable "storage_alarm_threshold_gb" {
  description = "Storage alarm threshold in GB"
  type        = number
  default     = 80
}

variable "search_error_threshold" {
  description = "Search error count threshold for alarms"
  type        = number
  default     = 100
}

variable "ocu_alarm_threshold" {
  description = "OCU usage threshold for alarms"
  type        = number
  default     = 8
}
