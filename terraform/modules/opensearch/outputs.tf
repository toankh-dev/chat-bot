# OpenSearch Serverless Module Outputs

# ============================================================================
# Collection Outputs
# ============================================================================

output "collection_id" {
  description = "ID of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.id
}

output "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.name
}

output "collection_arn" {
  description = "ARN of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.arn
}

output "collection_endpoint" {
  description = "Endpoint URL of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.collection_endpoint
}

output "dashboard_endpoint" {
  description = "Dashboard endpoint URL of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.dashboard_endpoint
}

# ============================================================================
# VPC Endpoint Outputs
# ============================================================================

output "vpc_endpoint_id" {
  description = "ID of the VPC endpoint (if created)"
  value       = var.create_vpc_endpoint ? aws_opensearchserverless_vpc_endpoint.main[0].id : null
}

output "vpc_endpoint_name" {
  description = "Name of the VPC endpoint (if created)"
  value       = var.create_vpc_endpoint ? aws_opensearchserverless_vpc_endpoint.main[0].name : null
}

# ============================================================================
# Connection Information
# ============================================================================

output "connection_info" {
  description = "Connection information for OpenSearch Serverless collection"
  value = {
    collection_id       = aws_opensearchserverless_collection.main.id
    collection_name     = aws_opensearchserverless_collection.main.name
    collection_endpoint = aws_opensearchserverless_collection.main.collection_endpoint
    region              = data.aws_region.current.name
  }
}
