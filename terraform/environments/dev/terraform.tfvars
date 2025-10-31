# ============================================================================
# Development Environment Configuration
# ============================================================================

# General
project_name = "kass-chatbot"
environment  = "dev"
aws_region   = "us-east-1"
owner        = "Platform Team"
cost_center  = "Engineering"

# VPC & Networking
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
enable_nat_gateway   = false # Use VPC endpoints to save cost

# VPC Endpoints
enable_bedrock_vpc_endpoint    = true
enable_opensearch_vpc_endpoint = true

# DynamoDB
enable_dynamodb_pitr  = false # Disable PITR in dev to save cost
dynamodb_billing_mode = "PAY_PER_REQUEST"

# OpenSearch
opensearch_max_ocu = 2 # Minimum for dev

# Bedrock Models
bedrock_llm_model_id   = "anthropic.claude-3-haiku-20240307-v1:0" # Use Haiku for dev (cheaper)
bedrock_embed_model_id = "amazon.titan-embed-text-v2:0"

# Lambda
lambda_runtime     = "python3.11"
lambda_timeout     = 300
lambda_memory_size = 512 # Lower memory for dev
log_level          = "DEBUG"
log_retention_days = 3

# API Gateway
api_throttle_burst_limit = 1000
api_throttle_rate_limit  = 100
enable_api_key_auth      = true
enable_cognito_auth      = false
api_cors_allow_origins   = ["*"]

# EventBridge
enable_daily_embeddings = false # Manual trigger in dev
embeddings_schedule     = "cron(0 2 * * ? *)"

# Monitoring
enable_xray_tracing       = true
enable_enhanced_monitoring = false
alarm_email               = ""

# RDS (Optional)
enable_rds              = false
rds_instance_class      = "db.t3.micro"
rds_allocated_storage   = 20
rds_database_name       = "kassdb_dev"
rds_master_username     = "kass_admin"
rds_backup_retention_period = 0 # No backups in dev

# Feature Flags
enable_discord_integration = true
enable_slack_integration   = false
enable_gitlab_integration  = false
enable_caching             = true
enable_rate_limiting       = false # No rate limiting in dev

# Security
allowed_ip_ranges = ["0.0.0.0/0"] # Allow all in dev
enable_waf        = false
