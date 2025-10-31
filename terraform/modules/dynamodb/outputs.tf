# ============================================================================
# DynamoDB Module Outputs
# ============================================================================

output "table_names" {
  description = "Map of table keys to table names"
  value       = { for k, v in aws_dynamodb_table.tables : k => v.name }
}

output "table_arns" {
  description = "Map of table keys to table ARNs"
  value       = { for k, v in aws_dynamodb_table.tables : k => v.arn }
}

output "table_ids" {
  description = "Map of table keys to table IDs"
  value       = { for k, v in aws_dynamodb_table.tables : k => v.id }
}

output "table_stream_arns" {
  description = "Map of table keys to stream ARNs (if streams enabled)"
  value       = { for k, v in aws_dynamodb_table.tables : k => v.stream_arn if v.stream_enabled }
}

output "table_stream_labels" {
  description = "Map of table keys to stream labels (if streams enabled)"
  value       = { for k, v in aws_dynamodb_table.tables : k => v.stream_label if v.stream_enabled }
}
