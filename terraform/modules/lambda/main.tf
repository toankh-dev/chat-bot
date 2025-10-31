# Lambda Module for KASS Chatbot
# Creates Lambda functions and layers

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
# Lambda Layers
# ============================================================================

# Common utilities layer (boto3, opensearch-py, etc.)
resource "aws_lambda_layer_version" "common_utilities" {
  count               = var.create_common_layer ? 1 : 0
  filename            = var.common_layer_zip_path
  layer_name          = "${var.name_prefix}-common-utilities"
  description         = "Common utilities for KASS Chatbot Lambda functions (boto3, opensearch-py, etc.)"
  compatible_runtimes = [var.python_runtime]
  source_code_hash    = filebase64sha256(var.common_layer_zip_path)

  lifecycle {
    create_before_destroy = true
  }
}

# LangChain layer
resource "aws_lambda_layer_version" "langchain" {
  count               = var.create_langchain_layer ? 1 : 0
  filename            = var.langchain_layer_zip_path
  layer_name          = "${var.name_prefix}-langchain"
  description         = "LangChain framework and dependencies"
  compatible_runtimes = [var.python_runtime]
  source_code_hash    = filebase64sha256(var.langchain_layer_zip_path)

  lifecycle {
    create_before_destroy = true
  }
}

# Document processing layer (pypdf, docx, etc.)
resource "aws_lambda_layer_version" "document_processing" {
  count               = var.create_document_layer ? 1 : 0
  filename            = var.document_layer_zip_path
  layer_name          = "${var.name_prefix}-document-processing"
  description         = "Document processing libraries (pypdf, python-docx, openpyxl)"
  compatible_runtimes = [var.python_runtime]
  source_code_hash    = filebase64sha256(var.document_layer_zip_path)

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================================================
# CloudWatch Log Groups (created before Lambda functions)
# ============================================================================

resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = var.lambda_functions

  name              = "/aws/lambda/${var.name_prefix}-${each.key}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name     = "${var.name_prefix}-${each.key}-logs"
    Function = each.key
  })
}

# ============================================================================
# Lambda Functions
# ============================================================================

resource "aws_lambda_function" "functions" {
  for_each = var.lambda_functions

  function_name = "${var.name_prefix}-${each.key}"
  description   = each.value.description
  role          = var.lambda_execution_role_arn

  filename         = each.value.zip_path
  source_code_hash = filebase64sha256(each.value.zip_path)
  handler          = each.value.handler
  runtime          = var.python_runtime

  timeout     = lookup(each.value, "timeout", var.default_timeout)
  memory_size = lookup(each.value, "memory_size", var.default_memory_size)

  # Environment variables
  environment {
    variables = merge(
      var.common_environment_variables,
      lookup(each.value, "environment_variables", {})
    )
  }

  # Layers
  layers = concat(
    var.create_common_layer ? [aws_lambda_layer_version.common_utilities[0].arn] : [],
    lookup(each.value, "use_langchain_layer", false) && var.create_langchain_layer ? [aws_lambda_layer_version.langchain[0].arn] : [],
    lookup(each.value, "use_document_layer", false) && var.create_document_layer ? [aws_lambda_layer_version.document_processing[0].arn] : [],
    lookup(each.value, "additional_layers", [])
  )

  # VPC configuration (if enabled)
  dynamic "vpc_config" {
    for_each = var.enable_vpc_config ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.security_group_ids
    }
  }

  # Tracing configuration
  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  # Reserved concurrent executions (if specified)
  reserved_concurrent_executions = lookup(each.value, "reserved_concurrent_executions", null)

  # Dead letter queue configuration (if specified)
  dynamic "dead_letter_config" {
    for_each = lookup(each.value, "dead_letter_queue_arn", null) != null ? [1] : []
    content {
      target_arn = each.value.dead_letter_queue_arn
    }
  }

  # Ephemeral storage (if specified)
  ephemeral_storage {
    size = lookup(each.value, "ephemeral_storage_size", 512)
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = merge(var.tags, {
    Name     = "${var.name_prefix}-${each.key}"
    Function = each.key
  })
}

# ============================================================================
# Lambda Permissions for API Gateway
# ============================================================================

resource "aws_lambda_permission" "api_gateway" {
  for_each = {
    for k, v in var.lambda_functions : k => v
    if lookup(v, "allow_api_gateway", false)
  }

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = var.api_gateway_execution_arn != "" ? "${var.api_gateway_execution_arn}/*/*" : null
}

# ============================================================================
# Lambda Permissions for EventBridge
# ============================================================================

resource "aws_lambda_permission" "eventbridge" {
  for_each = {
    for k, v in var.lambda_functions : k => v
    if lookup(v, "allow_eventbridge", false)
  }

  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions[each.key].function_name
  principal     = "events.amazonaws.com"
  source_arn    = var.eventbridge_rule_arn != "" ? var.eventbridge_rule_arn : null
}

# ============================================================================
# Lambda Permissions for S3
# ============================================================================

resource "aws_lambda_permission" "s3" {
  for_each = {
    for k, v in var.lambda_functions : k => v
    if lookup(v, "allow_s3", false)
  }

  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions[each.key].function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.s3_bucket_arn != "" ? var.s3_bucket_arn : null
}

# ============================================================================
# CloudWatch Alarms for Lambda Functions
# ============================================================================

# Alarm for function errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = var.enable_cloudwatch_alarms ? var.lambda_functions : {}

  alarm_name          = "${var.name_prefix}-${each.key}-errors-high"
  alarm_description   = "Lambda function ${each.key} has high error rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = lookup(each.value, "error_threshold", 10)
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.functions[each.key].function_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm for function throttles
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  for_each = var.enable_cloudwatch_alarms ? var.lambda_functions : {}

  alarm_name          = "${var.name_prefix}-${each.key}-throttles-high"
  alarm_description   = "Lambda function ${each.key} is being throttled"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = lookup(each.value, "throttle_threshold", 5)
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.functions[each.key].function_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm for function duration
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = var.enable_cloudwatch_alarms ? var.lambda_functions : {}

  alarm_name          = "${var.name_prefix}-${each.key}-duration-high"
  alarm_description   = "Lambda function ${each.key} has high duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = lookup(each.value, "timeout", var.default_timeout) * 1000 * 0.8  # 80% of timeout in ms
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.functions[each.key].function_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# ============================================================================
# Lambda Function URLs (Optional - for direct HTTP access)
# ============================================================================

resource "aws_lambda_function_url" "function_urls" {
  for_each = {
    for k, v in var.lambda_functions : k => v
    if lookup(v, "enable_function_url", false)
  }

  function_name      = aws_lambda_function.functions[each.key].function_name
  authorization_type = lookup(each.value, "function_url_auth_type", "AWS_IAM")

  dynamic "cors" {
    for_each = lookup(each.value, "enable_cors", false) ? [1] : []
    content {
      allow_credentials = lookup(each.value, "cors_allow_credentials", false)
      allow_origins     = lookup(each.value, "cors_allow_origins", ["*"])
      allow_methods     = lookup(each.value, "cors_allow_methods", ["GET", "POST"])
      allow_headers     = lookup(each.value, "cors_allow_headers", ["*"])
      max_age           = lookup(each.value, "cors_max_age", 86400)
    }
  }
}
