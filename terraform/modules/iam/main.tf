# IAM Module for KASS Chatbot
# Creates IAM roles and policies for Lambda functions and other AWS services

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Data source for current AWS region
data "aws_region" "current" {}

# ============================================================================
# Lambda Execution Role
# ============================================================================

resource "aws_iam_role" "lambda_execution" {
  name               = "${var.name_prefix}-lambda-execution"
  description        = "Execution role for KASS Chatbot Lambda functions"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-lambda-execution"
  })
}

# ============================================================================
# AWS Managed Policies
# ============================================================================

# Basic Lambda execution policy (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC execution policy (if Lambda is in VPC)
resource "aws_iam_role_policy_attachment" "lambda_vpc_execution" {
  count      = var.enable_vpc_access ? 1 : 0
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# X-Ray tracing policy
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  count      = var.enable_xray ? 1 : 0
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# ============================================================================
# Custom Policies
# ============================================================================

# Amazon Bedrock access policy
resource "aws_iam_role_policy" "bedrock_access" {
  name = "${var.name_prefix}-bedrock-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel"
        ]
        Resource = "*"
      }
    ]
  })
}

# OpenSearch Serverless access policy
resource "aws_iam_role_policy" "opensearch_access" {
  name = "${var.name_prefix}-opensearch-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = var.opensearch_collection_arn != "" ? var.opensearch_collection_arn : "*"
      },
      {
        Effect = "Allow"
        Action = [
          "aoss:ListCollections",
          "aoss:BatchGetCollection"
        ]
        Resource = "*"
      }
    ]
  })
}

# DynamoDB access policy
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "${var.name_prefix}-dynamodb-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          for table_arn in var.dynamodb_table_arns : table_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          for table_arn in var.dynamodb_table_arns : "${table_arn}/index/*"
        ]
      }
    ]
  })
}

# S3 access policy
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.name_prefix}-s3-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = concat(
          [for bucket_arn in var.s3_bucket_arns : bucket_arn],
          [for bucket_arn in var.s3_bucket_arns : "${bucket_arn}/*"]
        )
      }
    ]
  })
}

# Secrets Manager access policy (for API keys, credentials)
resource "aws_iam_role_policy" "secrets_manager_access" {
  count = var.enable_secrets_manager ? 1 : 0
  name  = "${var.name_prefix}-secrets-manager-access"
  role  = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.name_prefix}/*"
      }
    ]
  })
}

# Lambda invocation policy (for Lambda-to-Lambda calls)
resource "aws_iam_role_policy" "lambda_invocation" {
  name = "${var.name_prefix}-lambda-invocation"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.name_prefix}-*"
      }
    ]
  })
}

# ============================================================================
# API Gateway Execution Role
# ============================================================================

resource "aws_iam_role" "api_gateway_execution" {
  name               = "${var.name_prefix}-api-gateway-execution"
  description        = "Execution role for API Gateway to invoke Lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-gateway-execution"
  })
}

# API Gateway CloudWatch Logs policy
resource "aws_iam_role_policy" "api_gateway_cloudwatch" {
  name = "${var.name_prefix}-api-gateway-cloudwatch"
  role = aws_iam_role.api_gateway_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# API Gateway Lambda invocation policy
resource "aws_iam_role_policy" "api_gateway_lambda_invocation" {
  name = "${var.name_prefix}-api-gateway-lambda-invocation"
  role = aws_iam_role.api_gateway_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.name_prefix}-*"
      }
    ]
  })
}

# ============================================================================
# EventBridge Execution Role
# ============================================================================

resource "aws_iam_role" "eventbridge_execution" {
  name               = "${var.name_prefix}-eventbridge-execution"
  description        = "Execution role for EventBridge to invoke Lambda and other targets"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eventbridge-execution"
  })
}

# EventBridge Lambda invocation policy
resource "aws_iam_role_policy" "eventbridge_lambda_invocation" {
  name = "${var.name_prefix}-eventbridge-lambda-invocation"
  role = aws_iam_role.eventbridge_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.name_prefix}-*"
      }
    ]
  })
}

# ============================================================================
# S3 Event Notification Role (for Lambda triggers)
# ============================================================================

resource "aws_iam_role" "s3_event_lambda" {
  name               = "${var.name_prefix}-s3-event-lambda"
  description        = "Role for S3 to invoke Lambda on events"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-s3-event-lambda"
  })
}

# S3 Lambda invocation policy
resource "aws_iam_role_policy" "s3_lambda_invocation" {
  name = "${var.name_prefix}-s3-lambda-invocation"
  role = aws_iam_role.s3_event_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.name_prefix}-document-processor"
      }
    ]
  })
}
