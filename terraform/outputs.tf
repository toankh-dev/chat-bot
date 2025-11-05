# ============================================================================
# Terraform Outputs
# ============================================================================
# These outputs provide essential configuration values for Lambda functions
# and external integrations. Use these values to populate environment variables.

# ----------------------------------------------------------------------------
# Environment Information
# ----------------------------------------------------------------------------
output "environment" {
  description = "Deployment environment (dev/prod)"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

# ----------------------------------------------------------------------------
# DynamoDB Tables
# ----------------------------------------------------------------------------
output "dynamodb_tables" {
  description = "DynamoDB table names for Lambda environment variables"
  value = {
    conversations = module.dynamodb.table_names["conversations"]
    agent_state   = module.dynamodb.table_names["agent_state"]
    tool_logs     = module.dynamodb.table_names["tool_logs"]
  }
}

output "conversations_table_arn" {
  description = "Conversations table ARN"
  value       = module.dynamodb.table_arns["conversations"]
}

output "agent_state_table_arn" {
  description = "Agent state table ARN"
  value       = module.dynamodb.table_arns["agent_state"]
}

output "tool_logs_table_arn" {
  description = "Tool logs table ARN"
  value       = module.dynamodb.table_arns["tool_logs"]
}

# ----------------------------------------------------------------------------
# S3 Buckets
# ----------------------------------------------------------------------------
output "s3_buckets" {
  description = "S3 bucket names for Lambda environment variables"
  value = {
    documents  = module.s3.bucket_names["documents"]
    embeddings = module.s3.bucket_names["embeddings"]
    logs       = module.s3.bucket_names["logs"]
    backups    = module.s3.bucket_names["backups"]
  }
}

output "s3_bucket_arns" {
  description = "S3 bucket ARNs for IAM policies"
  value = {
    documents  = module.s3.bucket_arns["documents"]
    embeddings = module.s3.bucket_arns["embeddings"]
    logs       = module.s3.bucket_arns["logs"]
    backups    = module.s3.bucket_arns["backups"]
  }
}

# ----------------------------------------------------------------------------
# OpenSearch Serverless
# ----------------------------------------------------------------------------
output "opensearch_collection_endpoint" {
  description = "OpenSearch collection endpoint for Lambda environment variables"
  value       = module.opensearch.collection_endpoint
}

output "opensearch_collection_id" {
  description = "OpenSearch collection ID"
  value       = module.opensearch.collection_id
}

output "opensearch_collection_arn" {
  description = "OpenSearch collection ARN"
  value       = module.opensearch.collection_arn
}

# ----------------------------------------------------------------------------
# Lambda Functions
# ----------------------------------------------------------------------------
output "lambda_functions" {
  description = "Lambda function ARNs"
  value = {
    orchestrator       = module.lambda.function_arns["orchestrator"]
    vector_search      = module.lambda.function_arns["vector_search"]
    document_processor = module.lambda.function_arns["document_processor"]
    report_tool        = module.lambda.function_arns["report_tool"]
    summarize_tool     = module.lambda.function_arns["summarize_tool"]
    code_review_tool   = module.lambda.function_arns["code_review_tool"]
  }
}

output "lambda_function_urls" {
  description = "Lambda function URLs (if enabled)"
  value       = module.lambda.function_urls
  sensitive   = true
}

# ----------------------------------------------------------------------------
# API Gateway
# ----------------------------------------------------------------------------
output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = module.api_gateway.api_endpoint
}

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = module.api_gateway.api_id
}

# ----------------------------------------------------------------------------
# EventBridge
# ----------------------------------------------------------------------------
output "eventbridge_bus_arn" {
  description = "EventBridge event bus ARN"
  value       = module.eventbridge.event_bus_arn
}

output "eventbridge_bus_name" {
  description = "EventBridge event bus name for Lambda environment variables"
  value       = module.eventbridge.event_bus_name
}

# ----------------------------------------------------------------------------
# IAM Roles
# ----------------------------------------------------------------------------
output "lambda_execution_role_arn" {
  description = "Lambda execution role ARN"
  value       = module.iam.lambda_execution_role_arn
}

output "api_gateway_role_arn" {
  description = "API Gateway execution role ARN"
  value       = module.iam.api_gateway_role_arn
}

# ----------------------------------------------------------------------------
# VPC Configuration
# ----------------------------------------------------------------------------
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs for Lambda functions"
  value       = module.vpc.private_subnet_ids
}

output "security_group_id" {
  description = "Security group ID for Lambda functions"
  value       = module.vpc.lambda_security_group_id
}

# ----------------------------------------------------------------------------
# Bedrock Configuration
# ----------------------------------------------------------------------------
output "bedrock_configuration" {
  description = "Bedrock model configuration for Lambda environment variables"
  value = {
    llm_model_id   = var.bedrock_llm_model_id
    embed_model_id = var.bedrock_embed_model_id
    region         = var.aws_region
  }
}

# ----------------------------------------------------------------------------
# Complete Lambda Environment Variables
# ----------------------------------------------------------------------------
output "lambda_environment_variables" {
  description = "Complete environment variable configuration for Lambda functions"
  value = {
    ENVIRONMENT              = var.environment
    PROJECT_NAME             = var.project_name
    AWS_REGION              = var.aws_region

    # DynamoDB
    CONVERSATIONS_TABLE      = module.dynamodb.table_names["conversations"]
    AGENT_STATE_TABLE        = module.dynamodb.table_names["agent_state"]
    TOOL_LOGS_TABLE          = module.dynamodb.table_names["tool_logs"]

    # S3
    DOCUMENTS_BUCKET         = module.s3.bucket_names["documents"]
    EMBEDDINGS_BUCKET        = module.s3.bucket_names["embeddings"]
    LOGS_BUCKET              = module.s3.bucket_names["logs"]
    BACKUPS_BUCKET           = module.s3.bucket_names["backups"]

    # OpenSearch
    OPENSEARCH_ENDPOINT      = module.opensearch.collection_endpoint
    OPENSEARCH_COLLECTION_ID = module.opensearch.collection_id
    OPENSEARCH_INDEX         = "documents"

    # Bedrock
    LLM_PROVIDER            = "bedrock"
    BEDROCK_MODEL_ID        = var.bedrock_llm_model_id
    BEDROCK_EMBED_MODEL_ID  = var.bedrock_embed_model_id

    # EventBridge
    EVENTBUS_NAME           = module.eventbridge.event_bus_name

    # Logging
    LOG_LEVEL               = var.log_level
  }
  sensitive = false
}

# ----------------------------------------------------------------------------
# Deployment Summary
# ----------------------------------------------------------------------------
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = <<-EOT
    ============================================================
    KASS Chatbot Deployment Summary
    ============================================================
    Environment:     ${var.environment}
    Project:         ${var.project_name}
    Region:          ${var.aws_region}

    API Endpoint:    ${module.api_gateway.api_endpoint}

    DynamoDB Tables:
      - Conversations: ${module.dynamodb.table_names["conversations"]}
      - Agent State:   ${module.dynamodb.table_names["agent_state"]}
      - Tool Logs:     ${module.dynamodb.table_names["tool_logs"]}

    S3 Buckets:
      - Documents:     ${module.s3.bucket_names["documents"]}
      - Embeddings:    ${module.s3.bucket_names["embeddings"]}
      - Logs:          ${module.s3.bucket_names["logs"]}
      - Backups:       ${module.s3.bucket_names["backups"]}

    OpenSearch:
      - Endpoint:      ${module.opensearch.collection_endpoint}
      - Collection ID: ${module.opensearch.collection_id}

    Bedrock Models:
      - LLM:           ${var.bedrock_llm_model_id}
      - Embeddings:    ${var.bedrock_embed_model_id}

    Next Steps:
    1. Deploy Lambda functions: python scripts/lambda/deploy.py --env ${var.environment}
    2. Test API: curl ${module.api_gateway.api_endpoint}/health
    3. View logs: aws logs tail /aws/lambda/${var.project_name}-${var.environment}-orchestrator --follow
    ============================================================
  EOT
}
