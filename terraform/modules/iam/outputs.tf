# IAM Module Outputs

# ============================================================================
# Lambda Execution Role
# ============================================================================

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.name
}

output "lambda_execution_role_id" {
  description = "ID of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.id
}

# ============================================================================
# API Gateway Execution Role
# ============================================================================

output "api_gateway_execution_role_arn" {
  description = "ARN of the API Gateway execution role"
  value       = aws_iam_role.api_gateway_execution.arn
}

output "api_gateway_execution_role_name" {
  description = "Name of the API Gateway execution role"
  value       = aws_iam_role.api_gateway_execution.name
}

# ============================================================================
# EventBridge Execution Role
# ============================================================================

output "eventbridge_execution_role_arn" {
  description = "ARN of the EventBridge execution role"
  value       = aws_iam_role.eventbridge_execution.arn
}

output "eventbridge_execution_role_name" {
  description = "Name of the EventBridge execution role"
  value       = aws_iam_role.eventbridge_execution.name
}

# ============================================================================
# S3 Event Lambda Role
# ============================================================================

output "s3_event_lambda_role_arn" {
  description = "ARN of the S3 event Lambda role"
  value       = aws_iam_role.s3_event_lambda.arn
}

output "s3_event_lambda_role_name" {
  description = "Name of the S3 event Lambda role"
  value       = aws_iam_role.s3_event_lambda.name
}
