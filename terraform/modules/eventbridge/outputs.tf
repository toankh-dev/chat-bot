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
# Dynamic Rules Outputs
# ============================================================================

output "rule_arns" {
  description = "Map of EventBridge rule ARNs"
  value = {
    for rule_key, rule in aws_cloudwatch_event_rule.rules : rule_key => rule.arn
  }
}

output "rule_names" {
  description = "Map of EventBridge rule names"
  value = {
    for rule_key, rule in aws_cloudwatch_event_rule.rules : rule_key => rule.name
  }
}

output "configured_rules" {
  description = "List of configured EventBridge rules"
  value = [
    for rule_key, rule in var.rules : {
      name                = "${var.name_prefix}-${rule_key}"
      description         = rule.description
      has_event_pattern   = rule.event_pattern != null
      has_schedule        = rule.schedule_expression != null
      enabled             = rule.enabled
      target_count        = length(rule.targets)
    }
  ]
}

# ============================================================================
# Dead Letter Queue Outputs
# ============================================================================

output "dlq_arn" {
  description = "ARN of the Dead Letter Queue (if created)"
  value       = var.create_dlq ? aws_sqs_queue.dlq[0].arn : var.dlq_arn
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
# Lambda Permissions
# ============================================================================

output "lambda_permissions" {
  description = "Map of Lambda functions with EventBridge permissions"
  value = {
    for arn, function_name in local.lambda_permissions : function_name => arn
  }
}

# ============================================================================
# Configuration Summary
# ============================================================================

output "eventbridge_config" {
  description = "EventBridge configuration summary"
  value = {
    event_bus_name    = local.event_bus_name
    event_bus_arn     = local.event_bus_arn
    custom_event_bus  = var.create_custom_event_bus
    total_rules       = length(var.rules)
    dlq_enabled       = var.create_dlq
    logging_enabled   = var.enable_eventbridge_logging
    alarms_enabled    = var.enable_cloudwatch_alarms
    rules = {
      for rule_key, rule in var.rules : rule_key => {
        enabled      = rule.enabled
        type         = rule.schedule_expression != null ? "scheduled" : "event-driven"
        target_count = length(rule.targets)
      }
    }
  }
}
