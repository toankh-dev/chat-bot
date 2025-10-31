# Lambda Module Outputs

# ============================================================================
# Lambda Function Outputs
# ============================================================================

output "function_arns" {
  description = "Map of Lambda function ARNs"
  value = {
    for k, v in aws_lambda_function.functions : k => v.arn
  }
}

output "function_names" {
  description = "Map of Lambda function names"
  value = {
    for k, v in aws_lambda_function.functions : k => v.function_name
  }
}

output "function_invoke_arns" {
  description = "Map of Lambda function invoke ARNs (for API Gateway integration)"
  value = {
    for k, v in aws_lambda_function.functions : k => v.invoke_arn
  }
}

output "function_qualified_arns" {
  description = "Map of Lambda function qualified ARNs (with version)"
  value = {
    for k, v in aws_lambda_function.functions : k => v.qualified_arn
  }
}

output "function_versions" {
  description = "Map of Lambda function versions"
  value = {
    for k, v in aws_lambda_function.functions : k => v.version
  }
}

output "function_urls" {
  description = "Map of Lambda function URLs (if enabled)"
  value = {
    for k, v in aws_lambda_function_url.function_urls : k => v.function_url
  }
}

# ============================================================================
# Lambda Layer Outputs
# ============================================================================

output "common_layer_arn" {
  description = "ARN of the common utilities Lambda layer"
  value       = var.create_common_layer ? aws_lambda_layer_version.common_utilities[0].arn : null
}

output "common_layer_version" {
  description = "Version of the common utilities Lambda layer"
  value       = var.create_common_layer ? aws_lambda_layer_version.common_utilities[0].version : null
}

output "langchain_layer_arn" {
  description = "ARN of the LangChain Lambda layer"
  value       = var.create_langchain_layer ? aws_lambda_layer_version.langchain[0].arn : null
}

output "langchain_layer_version" {
  description = "Version of the LangChain Lambda layer"
  value       = var.create_langchain_layer ? aws_lambda_layer_version.langchain[0].version : null
}

output "document_layer_arn" {
  description = "ARN of the document processing Lambda layer"
  value       = var.create_document_layer ? aws_lambda_layer_version.document_processing[0].arn : null
}

output "document_layer_version" {
  description = "Version of the document processing Lambda layer"
  value       = var.create_document_layer ? aws_lambda_layer_version.document_processing[0].version : null
}

# ============================================================================
# CloudWatch Log Groups
# ============================================================================

output "log_group_names" {
  description = "Map of CloudWatch log group names"
  value = {
    for k, v in aws_cloudwatch_log_group.lambda_logs : k => v.name
  }
}

output "log_group_arns" {
  description = "Map of CloudWatch log group ARNs"
  value = {
    for k, v in aws_cloudwatch_log_group.lambda_logs : k => v.arn
  }
}

# ============================================================================
# Deployment Information
# ============================================================================

output "deployment_info" {
  description = "Deployment information for all Lambda functions"
  value = {
    for k, v in aws_lambda_function.functions : k => {
      function_name    = v.function_name
      function_arn     = v.arn
      invoke_arn       = v.invoke_arn
      version          = v.version
      last_modified    = v.last_modified
      runtime          = v.runtime
      timeout          = v.timeout
      memory_size      = v.memory_size
      log_group        = aws_cloudwatch_log_group.lambda_logs[k].name
      function_url     = lookup({ for fk, fv in aws_lambda_function_url.function_urls : fk => fv.function_url }, k, null)
    }
  }
}
