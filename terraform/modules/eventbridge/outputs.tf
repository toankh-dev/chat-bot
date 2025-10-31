# EventBridge Module Outputs

# ============================================================================
# Event Bus Outputs
# ============================================================================

output "event_bus_name" {
  description = "Name of the EventBridge event bus"
  value       = local.event_bus_name
}

output "event_bus_arn" {
  description = "ARN of the EventBridge event bus"
  value       = local.event_bus_arn
}

# ============================================================================
# Event Rules Outputs
# ============================================================================

output "document_uploaded_rule_arn" {
  description = "ARN of the document uploaded EventBridge rule"
  value       = aws_cloudwatch_event_rule.document_uploaded.arn
}

output "document_uploaded_rule_name" {
  description = "Name of the document uploaded EventBridge rule"
  value       = aws_cloudwatch_event_rule.document_uploaded.name
}

output "scheduled_data_fetch_rule_arn" {
  description = "ARN of the scheduled data fetch EventBridge rule (if enabled)"
  value       = var.enable_scheduled_fetch ? aws_cloudwatch_event_rule.scheduled_data_fetch[0].arn : null
}

output "scheduled_data_fetch_rule_name" {
  description = "Name of the scheduled data fetch EventBridge rule (if enabled)"
  value       = var.enable_scheduled_fetch ? aws_cloudwatch_event_rule.scheduled_data_fetch[0].name : null
}

output "scheduled_discord_fetch_rule_arn" {
  description = "ARN of the scheduled Discord fetch EventBridge rule (if enabled)"
  value       = var.enable_discord_fetch ? aws_cloudwatch_event_rule.scheduled_discord_fetch[0].arn : null
}

output "scheduled_discord_fetch_rule_name" {
  description = "Name of the scheduled Discord fetch EventBridge rule (if enabled)"
  value       = var.enable_discord_fetch ? aws_cloudwatch_event_rule.scheduled_discord_fetch[0].name : null
}

output "report_generation_rule_arn" {
  description = "ARN of the report generation EventBridge rule (if enabled)"
  value       = var.enable_report_generation ? aws_cloudwatch_event_rule.report_generation[0].arn : null
}

output "report_generation_rule_name" {
  description = "Name of the report generation EventBridge rule (if enabled)"
  value       = var.enable_report_generation ? aws_cloudwatch_event_rule.report_generation[0].name : null
}

output "cache_warming_rule_arn" {
  description = "ARN of the cache warming EventBridge rule (if enabled)"
  value       = var.enable_cache_warming ? aws_cloudwatch_event_rule.cache_warming[0].arn : null
}

output "cache_warming_rule_name" {
  description = "Name of the cache warming EventBridge rule (if enabled)"
  value       = var.enable_cache_warming ? aws_cloudwatch_event_rule.cache_warming[0].name : null
}

# ============================================================================
# Dead Letter Queue Outputs
# ============================================================================

output "dlq_arn" {
  description = "ARN of the Dead Letter Queue (if created)"
  value       = var.create_dlq ? aws_sqs_queue.dlq[0].arn : null
}

output "dlq_url" {
  description = "URL of the Dead Letter Queue (if created)"
  value       = var.create_dlq ? aws_sqs_queue.dlq[0].url : null
}

output "dlq_name" {
  description = "Name of the Dead Letter Queue (if created)"
  value       = var.create_dlq ? aws_sqs_queue.dlq[0].name : null
}

# ============================================================================
# CloudWatch Log Group
# ============================================================================

output "log_group_name" {
  description = "Name of the CloudWatch log group for EventBridge (if enabled)"
  value       = var.enable_eventbridge_logging ? aws_cloudwatch_log_group.eventbridge[0].name : null
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group for EventBridge (if enabled)"
  value       = var.enable_eventbridge_logging ? aws_cloudwatch_log_group.eventbridge[0].arn : null
}

# ============================================================================
# Configuration Information
# ============================================================================

output "eventbridge_config" {
  description = "EventBridge configuration information"
  value = {
    event_bus_name          = local.event_bus_name
    document_uploaded_rule  = aws_cloudwatch_event_rule.document_uploaded.name
    scheduled_fetch_enabled = var.enable_scheduled_fetch
    discord_fetch_enabled   = var.enable_discord_fetch
    report_gen_enabled      = var.enable_report_generation
    cache_warming_enabled   = var.enable_cache_warming
    dlq_enabled             = var.create_dlq
  }
}
