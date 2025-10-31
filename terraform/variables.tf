# ============================================================================
# Terraform Variables for KASS Chatbot
# ============================================================================

# ============================================================================
# General Variables
# ============================================================================

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "kass-chatbot"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "owner" {
  description = "Owner/team responsible for the resources"
  type        = string
  default     = "Platform Team"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "Engineering"
}

# ============================================================================
# VPC & Networking Variables
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnets"
  type        = bool
  default     = false # Use VPC endpoints instead to save cost
}

variable "enable_bedrock_vpc_endpoint" {
  description = "Enable VPC endpoint for Bedrock"
  type        = bool
  default     = true
}

variable "enable_opensearch_vpc_endpoint" {
  description = "Enable VPC endpoint for OpenSearch"
  type        = bool
  default     = true
}

# ============================================================================
# S3 Variables
# ============================================================================

variable "enable_s3_versioning" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_lifecycle_glacier_days" {
  description = "Days before transitioning to Glacier"
  type        = number
  default     = 90
}

variable "s3_lifecycle_expiration_days" {
  description = "Days before expiring objects"
  type        = number
  default     = 365
}

# ============================================================================
# DynamoDB Variables
# ============================================================================

variable "enable_dynamodb_pitr" {
  description = "Enable point-in-time recovery for DynamoDB"
  type        = bool
  default     = true
}

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

# ============================================================================
# OpenSearch Variables
# ============================================================================

variable "opensearch_max_ocu" {
  description = "Maximum OpenSearch Compute Units"
  type        = number
  default     = 4
}

variable "opensearch_engine_version" {
  description = "OpenSearch engine version"
  type        = string
  default     = "2.11"
}

# ============================================================================
# Bedrock Variables
# ============================================================================

variable "bedrock_llm_model_id" {
  description = "Bedrock LLM model ID"
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "bedrock_embed_model_id" {
  description = "Bedrock embedding model ID"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "bedrock_haiku_model_id" {
  description = "Bedrock Haiku model ID for simple queries"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

# ============================================================================
# Lambda Variables
# ============================================================================

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Default Lambda timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Default Lambda memory size in MB"
  type        = number
  default     = 1024
}

variable "lambda_reserved_concurrent_executions" {
  description = "Reserved concurrent executions for Lambda"
  type        = number
  default     = -1 # -1 means unreserved
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period"
  }
}

# ============================================================================
# API Gateway Variables
# ============================================================================

variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 5000
}

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit (requests per second)"
  type        = number
  default     = 10000
}

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
  description = "Cognito User Pool ARN for authentication"
  type        = string
  default     = ""
}

variable "api_cors_allow_origins" {
  description = "CORS allowed origins for API Gateway"
  type        = list(string)
  default     = ["*"]
}

# ============================================================================
# EventBridge Variables
# ============================================================================

variable "enable_daily_embeddings" {
  description = "Enable daily embeddings batch job"
  type        = bool
  default     = true
}

variable "embeddings_schedule" {
  description = "Cron schedule for embeddings job (UTC)"
  type        = string
  default     = "cron(0 2 * * ? *)" # 2 AM UTC daily
}

# ============================================================================
# Monitoring Variables
# ============================================================================

variable "enable_xray_tracing" {
  description = "Enable X-Ray tracing for Lambda"
  type        = bool
  default     = true
}

variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring"
  type        = bool
  default     = false
}

variable "alarm_email" {
  description = "Email for CloudWatch alarm notifications"
  type        = string
  default     = ""
}

# ============================================================================
# RDS Variables (Optional)
# ============================================================================

variable "enable_rds" {
  description = "Enable RDS PostgreSQL instance"
  type        = bool
  default     = false
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "rds_database_name" {
  description = "RDS database name"
  type        = string
  default     = "kassdb"
}

variable "rds_master_username" {
  description = "RDS master username"
  type        = string
  default     = "kass_admin"
  sensitive   = true
}

variable "rds_backup_retention_period" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 7
}

# ============================================================================
# Feature Flags
# ============================================================================

variable "enable_discord_integration" {
  description = "Enable Discord bot integration"
  type        = bool
  default     = true
}

variable "enable_slack_integration" {
  description = "Enable Slack integration"
  type        = bool
  default     = false
}

variable "enable_gitlab_integration" {
  description = "Enable GitLab integration"
  type        = bool
  default     = false
}

variable "enable_caching" {
  description = "Enable response caching in DynamoDB"
  type        = bool
  default     = true
}

variable "enable_rate_limiting" {
  description = "Enable rate limiting per user"
  type        = bool
  default     = true
}

# ============================================================================
# Security Variables
# ============================================================================

variable "allowed_ip_ranges" {
  description = "Allowed IP ranges for API access (CIDR notation)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Allow all by default, restrict in production
}

variable "enable_waf" {
  description = "Enable AWS WAF for API Gateway"
  type        = bool
  default     = false
}

variable "kms_key_deletion_window" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 30
}
