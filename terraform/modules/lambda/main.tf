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
# Local Variables
# ============================================================================

locals {
  # Convert simplified `functions` input into the internal `lambda_functions` structure
  lambda_functions_merged = {
    for name, cfg in var.functions : name => {
      description           = "Lambda function ${name}"
      handler               = cfg.handler
      zip_path              = "${path.module}/../../dist/functions/${name}.zip"
      timeout               = lookup(cfg, "timeout", var.default_timeout)
      memory_size           = lookup(cfg, "memory_size", var.default_memory_size)
      environment_variables = var.environment_variables
      runtime               = lookup(cfg, "runtime", var.python_runtime)
    }
  }

  # Convert simplified `layers` input into creation list (optional)
  custom_layers = [
    for layer in var.layers : {
      name                = layer.name
      description         = layer.description
      compatible_runtimes = layer.compatible_runtimes
    }
  ]
}

# ============================================================================
# CloudWatch Log Groups (created before Lambda functions)
# ============================================================================

resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = local.lambda_functions_merged

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
  for_each = local.lambda_functions_merged

  function_name = "${var.name_prefix}-${each.key}"
  description   = each.value.description
  role          = var.execution_role_arn

  filename         = each.value.zip_path
  source_code_hash = filebase64sha256(each.value.zip_path)
  handler          = each.value.handler
  runtime          = var.python_runtime

  timeout     = lookup(each.value, "timeout", var.default_timeout)
  memory_size = lookup(each.value, "memory_size", var.default_memory_size)

  # Environment variables
  environment {
    variables = merge(
      var.environment_variables,
      lookup(each.value, "environment_variables", {})
    )
  }

  # Layers
  layers = lookup(each.value, "layers", [])

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
    for k, v in local.lambda_functions_merged : k => v
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
    for k, v in local.lambda_functions_merged : k => v
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
    for k, v in local.lambda_functions_merged : k => v
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
  for_each = var.enable_cloudwatch_alarms ? local.lambda_functions_merged : {}

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
  for_each = var.enable_cloudwatch_alarms ? local.lambda_functions_merged : {}

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
  for_each = var.enable_cloudwatch_alarms ? local.lambda_functions_merged : {}

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
    for k, v in local.lambda_functions_merged : k => v
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
