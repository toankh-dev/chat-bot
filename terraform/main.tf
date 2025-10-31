# ============================================================================
# Main Terraform Configuration for KASS Chatbot on AWS
# ============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Backend configuration for state management
  backend "s3" {
    # Configuration provided via backend config file
    # Run: terraform init -backend-config=environments/dev/backend.tfvars
  }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  # Naming convention
  name_prefix = "${var.project_name}-${var.environment}"

  # Common tags
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Region      = local.region
  }

  # AZs for multi-AZ deployment
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# ============================================================================
# VPC & Networking Module
# ============================================================================

module "vpc" {
  source = "./modules/vpc"

  name_prefix         = local.name_prefix
  vpc_cidr            = var.vpc_cidr
  availability_zones  = local.azs
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  enable_nat_gateway  = var.enable_nat_gateway
  enable_vpn_gateway  = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  # VPC Endpoints
  enable_s3_endpoint       = true
  enable_dynamodb_endpoint = true
  enable_bedrock_endpoint  = var.enable_bedrock_vpc_endpoint
  enable_opensearch_endpoint = var.enable_opensearch_vpc_endpoint

  tags = local.common_tags
}

# ============================================================================
# S3 Buckets Module
# ============================================================================

module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix
  account_id  = local.account_id

  # Buckets to create
  buckets = {
    documents = {
      versioning_enabled = true
      lifecycle_rules = [
        {
          id      = "archive-old-documents"
          enabled = true
          transitions = [
            {
              days          = 90
              storage_class = "GLACIER"
            }
          ]
        }
      ]
    }
    embeddings = {
      versioning_enabled = false
      lifecycle_rules    = []
    }
    logs = {
      versioning_enabled = false
      lifecycle_rules = [
        {
          id      = "delete-old-logs"
          enabled = true
          expiration = {
            days = 30
          }
        }
      ]
    }
    backups = {
      versioning_enabled = true
      lifecycle_rules    = []
    }
  }

  # Enable event notifications
  enable_event_notifications = true
  lambda_processor_arn       = module.lambda.document_processor_arn

  tags = local.common_tags
}

# ============================================================================
# DynamoDB Tables Module
# ============================================================================

module "dynamodb" {
  source = "./modules/dynamodb"

  name_prefix = local.name_prefix

  # Tables configuration
  tables = {
    conversations = {
      hash_key       = "conversation_id"
      range_key      = "timestamp"
      billing_mode   = "PAY_PER_REQUEST"
      enable_streams = true
      ttl_enabled    = true
      ttl_attribute  = "ttl"

      attributes = [
        { name = "conversation_id", type = "S" },
        { name = "timestamp", type = "N" },
        { name = "user_id", type = "S" },
        { name = "created_at", type = "S" }
      ]

      global_secondary_indexes = [
        {
          name            = "user_id-index"
          hash_key        = "user_id"
          range_key       = "created_at"
          projection_type = "ALL"
        }
      ]
    }

    agent_state = {
      hash_key       = "agent_id"
      range_key      = "execution_id"
      billing_mode   = "PAY_PER_REQUEST"
      enable_streams = false
      ttl_enabled    = true
      ttl_attribute  = "ttl"

      attributes = [
        { name = "agent_id", type = "S" },
        { name = "execution_id", type = "S" }
      ]

      global_secondary_indexes = []
    }

    tool_logs = {
      hash_key       = "tool_id"
      range_key      = "timestamp"
      billing_mode   = "PAY_PER_REQUEST"
      enable_streams = false
      ttl_enabled    = true
      ttl_attribute  = "ttl"

      attributes = [
        { name = "tool_id", type = "S" },
        { name = "timestamp", type = "N" }
      ]

      global_secondary_indexes = []
    }
  }

  enable_point_in_time_recovery = var.enable_dynamodb_pitr

  tags = local.common_tags
}

# ============================================================================
# Amazon OpenSearch Serverless Module
# ============================================================================

module "opensearch" {
  source = "./modules/opensearch"

  name_prefix     = local.name_prefix
  collection_name = "${local.name_prefix}-vectors"
  collection_type = "VECTORSEARCH"

  # Capacity
  max_indexing_capacity_in_ocu = var.opensearch_max_ocu
  max_search_capacity_in_ocu   = var.opensearch_max_ocu

  # Network
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids

  # Security
  allowed_principals = [
    module.iam.lambda_execution_role_arn
  ]

  tags = local.common_tags
}

# ============================================================================
# IAM Roles & Policies Module
# ============================================================================

module "iam" {
  source = "./modules/iam"

  name_prefix = local.name_prefix
  account_id  = local.account_id
  region      = local.region

  # S3 buckets
  s3_bucket_arns = module.s3.bucket_arns

  # DynamoDB tables
  dynamodb_table_arns = module.dynamodb.table_arns

  # OpenSearch
  opensearch_collection_arn = module.opensearch.collection_arn

  # Bedrock
  enable_bedrock_access = true

  tags = local.common_tags
}

# ============================================================================
# Lambda Functions Module
# ============================================================================

module "lambda" {
  source = "./modules/lambda"

  name_prefix = local.name_prefix
  account_id  = local.account_id

  # Networking
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.vpc.lambda_security_group_id]

  # IAM
  execution_role_arn = module.iam.lambda_execution_role_arn

  # Environment variables
  environment_variables = {
    ENVIRONMENT              = var.environment
    AWS_ACCOUNT_ID           = local.account_id
    REGION                   = local.region
    OPENSEARCH_ENDPOINT      = module.opensearch.collection_endpoint
    OPENSEARCH_COLLECTION_ID = module.opensearch.collection_id
    CONVERSATIONS_TABLE      = module.dynamodb.table_names["conversations"]
    AGENT_STATE_TABLE        = module.dynamodb.table_names["agent_state"]
    TOOL_LOGS_TABLE          = module.dynamodb.table_names["tool_logs"]
    DOCUMENTS_BUCKET         = module.s3.bucket_names["documents"]
    EMBEDDINGS_BUCKET        = module.s3.bucket_names["embeddings"]
    BEDROCK_MODEL_ID         = var.bedrock_llm_model_id
    BEDROCK_EMBED_MODEL_ID   = var.bedrock_embed_model_id
    LOG_LEVEL                = var.log_level
  }

  # Lambda functions configuration
  functions = {
    orchestrator = {
      handler     = "orchestrator.handler"
      memory_size = 1024
      timeout     = 300
      runtime     = "python3.11"
    }
    vector_search = {
      handler     = "vector_search.handler"
      memory_size = 512
      timeout     = 30
      runtime     = "python3.11"
    }
    document_processor = {
      handler     = "document_processor.handler"
      memory_size = 3008
      timeout     = 900
      runtime     = "python3.11"
    }
    report_tool = {
      handler     = "tools/report_tool.handler"
      memory_size = 512
      timeout     = 60
      runtime     = "python3.11"
    }
    summarize_tool = {
      handler     = "tools/summarize_tool.handler"
      memory_size = 512
      timeout     = 120
      runtime     = "python3.11"
    }
    code_review_tool = {
      handler     = "tools/code_review_tool.handler"
      memory_size = 512
      timeout     = 120
      runtime     = "python3.11"
    }
    discord_handler = {
      handler     = "discord_handler.handler"
      memory_size = 512
      timeout     = 30
      runtime     = "python3.11"
    }
  }

  # Lambda layers
  layers = [
    {
      name        = "langchain-layer"
      description = "LangChain and dependencies"
      compatible_runtimes = ["python3.11"]
    },
    {
      name        = "aws-sdk-layer"
      description = "AWS SDK and boto3"
      compatible_runtimes = ["python3.11"]
    },
    {
      name        = "data-processing-layer"
      description = "Pandas, openpyxl, and data processing libraries"
      compatible_runtimes = ["python3.11"]
    }
  ]

  tags = local.common_tags
}

# ============================================================================
# API Gateway Module
# ============================================================================

module "api_gateway" {
  source = "./modules/api_gateway"

  name_prefix = local.name_prefix

  # API Configuration
  api_name        = "${local.name_prefix}-api"
  api_description = "KASS Chatbot REST API"
  stage_name      = var.environment

  # Lambda integrations
  lambda_integrations = {
    "POST /chat" = {
      lambda_arn         = module.lambda.function_arns["orchestrator"]
      lambda_invoke_arn  = module.lambda.function_invoke_arns["orchestrator"]
      timeout_milliseconds = 29000
    }
    "POST /search" = {
      lambda_arn         = module.lambda.function_arns["vector_search"]
      lambda_invoke_arn  = module.lambda.function_invoke_arns["vector_search"]
      timeout_milliseconds = 29000
    }
    "GET /conversations/{user_id}" = {
      lambda_arn         = module.lambda.function_arns["orchestrator"]
      lambda_invoke_arn  = module.lambda.function_invoke_arns["orchestrator"]
      timeout_milliseconds = 29000
    }
    "GET /conversation/{conversation_id}" = {
      lambda_arn         = module.lambda.function_arns["orchestrator"]
      lambda_invoke_arn  = module.lambda.function_invoke_arns["orchestrator"]
      timeout_milliseconds = 29000
    }
    "DELETE /conversation/{conversation_id}" = {
      lambda_arn         = module.lambda.function_arns["orchestrator"]
      lambda_invoke_arn  = module.lambda.function_invoke_arns["orchestrator"]
      timeout_milliseconds = 29000
    }
    "GET /health" = {
      lambda_arn         = module.lambda.function_arns["orchestrator"]
      lambda_invoke_arn  = module.lambda.function_invoke_arns["orchestrator"]
      timeout_milliseconds = 5000
    }
  }

  # Throttling
  throttle_burst_limit = var.api_throttle_burst_limit
  throttle_rate_limit  = var.api_throttle_rate_limit

  # Authentication
  enable_api_key_auth = var.enable_api_key_auth
  enable_cognito_auth = var.enable_cognito_auth
  cognito_user_pool_arn = var.cognito_user_pool_arn

  # CORS
  cors_configuration = {
    allow_origins = var.api_cors_allow_origins
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Api-Key"]
    max_age       = 300
  }

  # Logging
  enable_access_logging   = true
  enable_execution_logging = true
  log_retention_days      = var.log_retention_days

  tags = local.common_tags
}

# ============================================================================
# EventBridge Module
# ============================================================================

module "eventbridge" {
  source = "./modules/eventbridge"

  name_prefix = local.name_prefix

  # Event rules
  rules = {
    document_upload = {
      description         = "Trigger document processor on S3 upload"
      event_pattern = jsonencode({
        source      = ["aws.s3"]
        detail-type = ["Object Created"]
        detail = {
          bucket = {
            name = [module.s3.bucket_names["documents"]]
          }
        }
      })
      targets = [
        {
          arn = module.lambda.function_arns["document_processor"]
        }
      ]
    }

    daily_embeddings = {
      description   = "Daily batch embedding job"
      schedule_expression = "cron(0 2 * * ? *)" # 2 AM UTC daily
      targets = [
        {
          arn = module.lambda.function_arns["document_processor"]
          input = jsonencode({
            batch_mode = true
            source     = "scheduled"
          })
        }
      ]
    }

    discord_events = {
      description   = "Handle Discord webhook events"
      event_pattern = jsonencode({
        source      = ["custom.discord"]
        detail-type = ["Discord Message", "Discord Command"]
      })
      targets = [
        {
          arn = module.lambda.function_arns["discord_handler"]
        }
      ]
    }
  }

  # Lambda permissions
  lambda_function_arns = module.lambda.function_arns

  tags = local.common_tags
}

# ============================================================================
# Outputs
# ============================================================================

output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = module.api_gateway.api_invoke_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = module.api_gateway.api_id
}

output "opensearch_endpoint" {
  description = "OpenSearch Serverless collection endpoint"
  value       = module.opensearch.collection_endpoint
}

output "opensearch_dashboard_url" {
  description = "OpenSearch dashboard URL"
  value       = module.opensearch.dashboard_url
}

output "s3_bucket_names" {
  description = "S3 bucket names"
  value       = module.s3.bucket_names
}

output "dynamodb_table_names" {
  description = "DynamoDB table names"
  value       = module.dynamodb.table_names
}

output "lambda_function_arns" {
  description = "Lambda function ARNs"
  value       = module.lambda.function_arns
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}
