# OpenSearch Serverless Module for KASS Chatbot
# Creates OpenSearch Serverless collection for vector search

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

locals {
  short_name_prefix = substr(var.name_prefix, 0, 16)
}

# ============================================================================
# VPC Endpoint (must be created BEFORE network policy for private access)
# ============================================================================

resource "aws_opensearchserverless_vpc_endpoint" "main" {
  count      = var.create_vpc_endpoint ? 1 : 0
  name       = "${local.short_name_prefix}-vpc-endpoint"
  subnet_ids = var.subnet_ids
  vpc_id     = var.vpc_id

  security_group_ids = var.security_group_ids
}

# ============================================================================
# Encryption Policy
# ============================================================================

resource "aws_opensearchserverless_security_policy" "encryption" {
  name        = "${local.short_name_prefix}-policy"
  type        = "encryption"
  description = "Encryption policy for ${local.short_name_prefix} OpenSearch Serverless collection"

  policy = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/${var.collection_name}"
        ]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

# ============================================================================
# Network Policy
# ============================================================================

resource "aws_opensearchserverless_security_policy" "network" {
  name        = "${local.short_name_prefix}-network-policy"
  type        = "network"
  description = "Network policy for ${local.short_name_prefix} OpenSearch Serverless collection"

  # For private access, use the VPC endpoint created by this module
  # For external VPC endpoints, use the provided vpc_endpoint_ids
  policy = var.allow_public_access ? jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.collection_name}"
          ]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = true
    }
    ]) : jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.collection_name}"
          ]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = false
      SourceVPCEs = var.create_vpc_endpoint ? [
        aws_opensearchserverless_vpc_endpoint.main[0].id
      ] : var.vpc_endpoint_ids
    }
  ])

  # Network policy must wait for VPC endpoint if we're creating one
  depends_on = [
    aws_opensearchserverless_vpc_endpoint.main
  ]
}

# ============================================================================
# OpenSearch Serverless Collection
# ============================================================================

resource "aws_opensearchserverless_collection" "main" {
  name        = var.collection_name
  description = var.collection_description
  type        = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network
  ]

  tags = merge(var.tags, {
    Name = var.collection_name
  })
}

# ============================================================================
# Data Access Policy
# ============================================================================

# Data access policy for Lambda execution role
resource "aws_opensearchserverless_access_policy" "lambda_access" {
  name        = "${local.short_name_prefix}-lambda-access"
  type        = "data"
  description = "Data access policy for Lambda functions to access OpenSearch collection"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.collection_name}"
          ]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
          ResourceType = "collection"
        },
        {
          Resource = [
            "index/${var.collection_name}/*"
          ]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument",
            "aoss:UpdateIndex",
            "aoss:DeleteIndex"
          ]
          ResourceType = "index"
        }
      ]
      Principal = var.lambda_execution_role_arns
    }
  ])

  depends_on = [
    aws_opensearchserverless_collection.main
  ]
}

# Data access policy for admin users (optional)
resource "aws_opensearchserverless_access_policy" "admin_access" {
  count       = length(var.admin_user_arns) > 0 ? 1 : 0
  name        = "${local.short_name_prefix}-admin-access-policy"
  type        = "data"
  description = "Data access policy for admin users to access OpenSearch collection"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.collection_name}"
          ]
          Permission = [
            "aoss:*"
          ]
          ResourceType = "collection"
        },
        {
          Resource = [
            "index/${var.collection_name}/*"
          ]
          Permission = [
            "aoss:*"
          ]
          ResourceType = "index"
        }
      ]
      Principal = var.admin_user_arns
    }
  ])

  depends_on = [
    aws_opensearchserverless_collection.main
  ]
}

# ============================================================================
# CloudWatch Alarms (Optional - for monitoring)
# ============================================================================

# Alarm for collection storage
resource "aws_cloudwatch_metric_alarm" "storage_high" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${local.short_name_prefix}-opensearch-storage-high"
  alarm_description   = "OpenSearch collection storage is high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "StorageUsed"
  namespace           = "AWS/AOSS"
  period              = 300
  statistic           = "Average"
  threshold           = var.storage_alarm_threshold_gb * 1024 * 1024 * 1024 # Convert GB to bytes
  treat_missing_data  = "notBreaching"

  dimensions = {
    CollectionId   = aws_opensearchserverless_collection.main.id
    CollectionName = var.collection_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm for search request errors
resource "aws_cloudwatch_metric_alarm" "search_errors_high" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${local.short_name_prefix}-opensearch-search-errors-high"
  alarm_description   = "OpenSearch collection has high search error rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "SearchRequestErrors"
  namespace           = "AWS/AOSS"
  period              = 300
  statistic           = "Sum"
  threshold           = var.search_error_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    CollectionId   = aws_opensearchserverless_collection.main.id
    CollectionName = var.collection_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm for OCU usage
resource "aws_cloudwatch_metric_alarm" "ocu_high" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${local.short_name_prefix}-opensearch-ocu-high"
  alarm_description   = "OpenSearch collection OCU usage is high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "SearchOCU"
  namespace           = "AWS/AOSS"
  period              = 300
  statistic           = "Average"
  threshold           = var.ocu_alarm_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    CollectionId   = aws_opensearchserverless_collection.main.id
    CollectionName = var.collection_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}
