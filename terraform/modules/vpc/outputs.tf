# ============================================================================
# VPC Module Outputs
# ============================================================================

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  value       = aws_security_group.lambda.id
}

output "opensearch_security_group_id" {
  description = "Security group ID for OpenSearch"
  value       = aws_security_group.opensearch.id
}

output "rds_security_group_id" {
  description = "Security group ID for RDS (if created)"
  value       = var.create_rds_security_group ? aws_security_group.rds[0].id : null
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "s3_endpoint_id" {
  description = "S3 VPC endpoint ID"
  value       = var.enable_s3_endpoint ? aws_vpc_endpoint.s3[0].id : null
}

output "dynamodb_endpoint_id" {
  description = "DynamoDB VPC endpoint ID"
  value       = var.enable_dynamodb_endpoint ? aws_vpc_endpoint.dynamodb[0].id : null
}

output "bedrock_endpoint_id" {
  description = "Bedrock VPC endpoint ID"
  value       = var.enable_bedrock_endpoint ? aws_vpc_endpoint.bedrock[0].id : null
}

output "opensearch_endpoint_id" {
  description = "OpenSearch VPC endpoint ID"
  value       = var.enable_opensearch_endpoint ? aws_vpc_endpoint.opensearch[0].id : null
}
