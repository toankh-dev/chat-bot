# API Gateway Module Outputs

# ============================================================================
# API Gateway Outputs
# ============================================================================

output "api_id" {
  description = "ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_arn" {
  description = "ARN of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.arn
}

output "api_name" {
  description = "Name of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.name
}

output "api_root_resource_id" {
  description = "Root resource ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.root_resource_id
}

output "api_execution_arn" {
  description = "Execution ARN of the API Gateway REST API (for Lambda permissions)"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

# ============================================================================
# Stage Outputs
# ============================================================================

output "stage_name" {
  description = "Name of the API Gateway stage"
  value       = aws_api_gateway_stage.main.stage_name
}

output "stage_arn" {
  description = "ARN of the API Gateway stage"
  value       = aws_api_gateway_stage.main.arn
}

output "stage_invoke_url" {
  description = "Invoke URL of the API Gateway stage"
  value       = aws_api_gateway_stage.main.invoke_url
}

# ============================================================================
# Endpoint URLs
# ============================================================================

output "api_url" {
  description = "Base URL of the API Gateway"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "chat_endpoint" {
  description = "URL of the /chat endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/chat"
}

output "search_endpoint" {
  description = "URL of the /search endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/search"
}

output "health_endpoint" {
  description = "URL of the /health endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/health"
}

# ============================================================================
# API Key Outputs
# ============================================================================

output "api_key_id" {
  description = "ID of the API key (if enabled)"
  value       = var.enable_api_key ? aws_api_gateway_api_key.main[0].id : null
}

output "api_key_value" {
  description = "Value of the API key (sensitive, if enabled)"
  value       = var.enable_api_key ? aws_api_gateway_api_key.main[0].value : null
  sensitive   = true
}

output "usage_plan_id" {
  description = "ID of the usage plan (if enabled)"
  value       = var.enable_api_key ? aws_api_gateway_usage_plan.main[0].id : null
}

# ============================================================================
# Deployment Information
# ============================================================================

output "deployment_id" {
  description = "ID of the API Gateway deployment"
  value       = aws_api_gateway_deployment.main.id
}

output "deployment_info" {
  description = "Deployment information for the API Gateway"
  value = {
    api_id        = aws_api_gateway_rest_api.main.id
    api_name      = aws_api_gateway_rest_api.main.name
    stage_name    = aws_api_gateway_stage.main.stage_name
    invoke_url    = aws_api_gateway_stage.main.invoke_url
    deployment_id = aws_api_gateway_deployment.main.id
    endpoints = {
      chat   = "${aws_api_gateway_stage.main.invoke_url}/chat"
      search = "${aws_api_gateway_stage.main.invoke_url}/search"
      health = "${aws_api_gateway_stage.main.invoke_url}/health"
    }
  }
}

# ============================================================================
# CloudWatch Log Group
# ============================================================================

output "log_group_name" {
  description = "Name of the CloudWatch log group for API Gateway"
  value       = aws_cloudwatch_log_group.api_gateway.name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group for API Gateway"
  value       = aws_cloudwatch_log_group.api_gateway.arn
}
