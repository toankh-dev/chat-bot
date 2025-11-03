# API Gateway Module for KASS Chatbot
# Creates REST API with Lambda integrations using dynamic configuration

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ============================================================================
# API Gateway CloudWatch Logs Role (Account-level)
# ============================================================================

# IAM role for API Gateway to write to CloudWatch Logs
resource "aws_iam_role" "cloudwatch" {
  count = var.enable_execution_logging ? 1 : 0
  name  = "${var.name_prefix}-apigateway-cloudwatch-role"

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

  tags = var.tags
}

# Attach AWS managed policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "cloudwatch" {
  count      = var.enable_execution_logging ? 1 : 0
  role       = aws_iam_role.cloudwatch[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# Set the CloudWatch Logs role ARN in API Gateway account settings
resource "aws_api_gateway_account" "main" {
  count               = var.enable_execution_logging ? 1 : 0
  cloudwatch_role_arn = aws_iam_role.cloudwatch[0].arn

  depends_on = [aws_iam_role_policy_attachment.cloudwatch]
}

# ============================================================================
# Local Variables for Route Parsing
# ============================================================================

locals {
  # Parse routes from lambda_integrations keys (e.g., "POST /chat" -> method: POST, path: /chat)
  routes = {
    for route_key, config in var.lambda_integrations : route_key => {
      method           = split(" ", route_key)[0]
      path             = split(" ", route_key)[1]
      path_parts       = split("/", trimprefix(split(" ", route_key)[1], "/"))
      lambda_arn       = config.lambda_arn
      lambda_invoke_arn = config.lambda_invoke_arn
      timeout_ms       = config.timeout_milliseconds
      authorization    = config.authorization
      api_key_required = config.api_key_required
    }
  }

  # Group routes by path for resource creation
  unique_paths = distinct([for route in local.routes : route.path])

  # Create path hierarchy (e.g., /conversation/{id} needs both /conversation and /conversation/{id})
  path_segments = flatten([
    for path in local.unique_paths : [
      for i in range(1, length(split("/", trimprefix(path, "/"))) + 1) :
        "/${join("/", slice(split("/", trimprefix(path, "/")), 0, i))}"
    ]
  ])

  unique_path_segments = distinct(local.path_segments)
}

# ============================================================================
# REST API
# ============================================================================

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.name_prefix}-api"
  description = var.api_description

  endpoint_configuration {
    types = [var.endpoint_type]
  }

  minimum_compression_size = var.minimum_compression_size

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api"
  })
}

# ============================================================================
# Cognito Authorizer (if enabled)
# ============================================================================

resource "aws_api_gateway_authorizer" "cognito" {
  count = var.enable_cognito_auth && var.cognito_user_pool_arn != "" ? 1 : 0

  name          = "${var.name_prefix}-cognito-authorizer"
  type          = "COGNITO_USER_POOLS"
  rest_api_id   = aws_api_gateway_rest_api.main.id
  provider_arns = [var.cognito_user_pool_arn]
}

# ============================================================================
# Dynamic API Gateway Resources
# Split into levels to avoid circular dependencies
# ============================================================================

# Level 1: Top-level paths (e.g., /chat, /conversation, /conversations)
resource "aws_api_gateway_resource" "paths_level_1" {
  for_each = toset([
    for path in local.unique_path_segments :
    path if path != "/" && can(regex("^/[^/]+$", path))
  ])

  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = regex("/([^/]+)$", each.value)[0]
}

# Level 2: Nested paths (e.g., /conversation/{id}, /conversations/{user_id})
resource "aws_api_gateway_resource" "paths_level_2" {
  for_each = toset([
    for path in local.unique_path_segments :
    path if path != "/" && !can(regex("^/[^/]+$", path))
  ])

  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.paths_level_1[regex("^(.+)/[^/]+$", each.value)[0]].id
  path_part   = regex("/([^/]+)$", each.value)[0]

  depends_on = [aws_api_gateway_resource.paths_level_1]
}

# Combine both levels for easier reference
locals {
  all_path_resources = merge(
    { for k, v in aws_api_gateway_resource.paths_level_1 : k => v },
    { for k, v in aws_api_gateway_resource.paths_level_2 : k => v }
  )
}

# ============================================================================
# Dynamic API Gateway Methods
# ============================================================================

resource "aws_api_gateway_method" "routes" {
  for_each = local.routes

  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = each.value.path == "/" ? aws_api_gateway_rest_api.main.root_resource_id : local.all_path_resources[each.value.path].id
  http_method   = each.value.method

  authorization = var.enable_cognito_auth && var.cognito_user_pool_arn != "" ? "COGNITO_USER_POOLS" : each.value.authorization
  authorizer_id = var.enable_cognito_auth && var.cognito_user_pool_arn != "" ? aws_api_gateway_authorizer.cognito[0].id : null

  api_key_required = var.enable_api_key_auth ? true : each.value.api_key_required

  request_parameters = {
    for param in regexall("\\{([^}]+)\\}", each.value.path) :
    "method.request.path.${param[0]}" => true
  }
}

# ============================================================================
# Dynamic Lambda Integrations
# ============================================================================

resource "aws_api_gateway_integration" "routes" {
  for_each = local.routes

  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = each.value.path == "/" ? aws_api_gateway_rest_api.main.root_resource_id : local.all_path_resources[each.value.path].id
  http_method             = aws_api_gateway_method.routes[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = each.value.lambda_invoke_arn
  timeout_milliseconds    = each.value.timeout_ms

  depends_on = [aws_api_gateway_method.routes]
}

# ============================================================================
# Lambda Permissions for API Gateway
# ============================================================================

resource "aws_lambda_permission" "api_gateway" {
  for_each = local.routes

  # Sanitize statement_id: only alphanumeric, underscores, and dashes allowed
  # Examples:
  #   "POST /chat" → "AllowAPIGatewayInvoke-POST-chat"
  #   "GET /conversations/{user_id}" → "AllowAPIGatewayInvoke-GET-conversations-user_id"
  statement_id  = "AllowAPIGatewayInvoke-${replace(replace(replace(replace(each.key, "/", "-"), " ", "-"), "{", ""), "}", "")}"
  action        = "lambda:InvokeFunction"
  function_name = split(":", each.value.lambda_arn)[6] # Extract function name from ARN
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# ============================================================================
# CORS Support - OPTIONS Methods
# ============================================================================

resource "aws_api_gateway_method" "cors_options" {
  for_each = toset(local.unique_paths)

  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = each.value == "/" ? aws_api_gateway_rest_api.main.root_resource_id : local.all_path_resources[each.value].id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "cors_options" {
  for_each = toset(local.unique_paths)

  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = each.value == "/" ? aws_api_gateway_rest_api.main.root_resource_id : local.all_path_resources[each.value].id
  http_method = aws_api_gateway_method.cors_options[each.value].http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({ statusCode = 200 })
  }

  depends_on = [aws_api_gateway_method.cors_options]
}

resource "aws_api_gateway_method_response" "cors_options" {
  for_each = toset(local.unique_paths)

  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = each.value == "/" ? aws_api_gateway_rest_api.main.root_resource_id : local.all_path_resources[each.value].id
  http_method = aws_api_gateway_method.cors_options[each.value].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }

  depends_on = [aws_api_gateway_method.cors_options]
}

resource "aws_api_gateway_integration_response" "cors_options" {
  for_each = toset(local.unique_paths)

  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = each.value == "/" ? aws_api_gateway_rest_api.main.root_resource_id : local.all_path_resources[each.value].id
  http_method = aws_api_gateway_method.cors_options[each.value].http_method
  status_code = aws_api_gateway_method_response.cors_options[each.value].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'${join(",", var.cors_configuration.allow_headers)}'"
    "method.response.header.Access-Control-Allow-Methods" = "'${join(",", var.cors_configuration.allow_methods)}'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${join(",", var.cors_configuration.allow_origins)}'"
  }

  depends_on = [
    aws_api_gateway_integration.cors_options,
    aws_api_gateway_method_response.cors_options
  ]
}

# ============================================================================
# API Gateway Deployment
# ============================================================================

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.main.body,
      jsonencode(local.routes),
      jsonencode(var.cors_configuration),
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.routes,
    aws_api_gateway_integration.cors_options,
  ]
}

# ============================================================================
# CloudWatch Log Group for API Gateway
# ============================================================================

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-gateway-logs"
  })
}

# ============================================================================
# API Gateway Stage
# ============================================================================

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.stage_name

  # Access logging
  dynamic "access_log_settings" {
    for_each = var.enable_access_logging ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.api_gateway.arn
      format = jsonencode({
        requestId      = "$context.requestId"
        ip             = "$context.identity.sourceIp"
        caller         = "$context.identity.caller"
        user           = "$context.identity.user"
        requestTime    = "$context.requestTime"
        httpMethod     = "$context.httpMethod"
        resourcePath   = "$context.resourcePath"
        status         = "$context.status"
        protocol       = "$context.protocol"
        responseLength = "$context.responseLength"
        errorMessage   = "$context.error.message"
        errorType      = "$context.error.messageString"
      })
    }
  }

  # X-Ray tracing
  xray_tracing_enabled = var.enable_xray

  # Cache settings
  cache_cluster_enabled = var.enable_cache
  cache_cluster_size    = var.enable_cache ? var.cache_size : null

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${var.stage_name}"
  })

  # Ensure account settings are configured before enabling logging
  depends_on = [
    aws_api_gateway_account.main
  ]
}

# ============================================================================
# API Gateway Method Settings
# ============================================================================

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    # Logging
    logging_level      = var.enable_execution_logging ? var.logging_level : "OFF"
    data_trace_enabled = var.enable_data_trace
    metrics_enabled    = var.enable_metrics

    # Throttling
    throttling_rate_limit  = var.throttle_rate_limit
    throttling_burst_limit = var.throttle_burst_limit

    # Caching
    caching_enabled                             = var.enable_cache
    cache_ttl_in_seconds                        = var.enable_cache ? var.cache_ttl_seconds : null
    cache_data_encrypted                        = var.enable_cache ? true : null
    require_authorization_for_cache_control     = var.enable_cache ? true : null
  }
}

# ============================================================================
# API Key and Usage Plan
# ============================================================================

resource "aws_api_gateway_api_key" "main" {
  count   = var.enable_api_key_auth ? 1 : 0
  name    = "${var.name_prefix}-api-key"
  enabled = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-key"
  })
}

resource "aws_api_gateway_usage_plan" "main" {
  count = var.enable_api_key_auth ? 1 : 0
  name  = "${var.name_prefix}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  throttle_settings {
    rate_limit  = var.usage_plan_rate_limit
    burst_limit = var.usage_plan_burst_limit
  }

  quota_settings {
    limit  = var.usage_plan_quota_limit
    period = var.usage_plan_quota_period
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-usage-plan"
  })
}

resource "aws_api_gateway_usage_plan_key" "main" {
  count         = var.enable_api_key_auth ? 1 : 0
  key_id        = aws_api_gateway_api_key.main[0].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main[0].id
}

# ============================================================================
# CloudWatch Alarms
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-api-4xx-errors-high"
  alarm_description   = "API Gateway has high 4XX error rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = var.error_4xx_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
    Stage   = aws_api_gateway_stage.main.stage_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-api-5xx-errors-high"
  alarm_description   = "API Gateway has high 5XX error rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = var.error_5xx_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
    Stage   = aws_api_gateway_stage.main.stage_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "api_latency" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-api-latency-high"
  alarm_description   = "API Gateway has high latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Average"
  threshold           = var.latency_threshold_ms
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
    Stage   = aws_api_gateway_stage.main.stage_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}
