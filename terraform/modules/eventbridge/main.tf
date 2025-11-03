# EventBridge Module for KASS Chatbot
# Creates EventBridge rules dynamically for async processing

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
# Local Variables
# ============================================================================

locals {
  event_bus_name = var.create_custom_event_bus ? aws_cloudwatch_event_bus.main[0].name : "default"
  event_bus_arn  = var.create_custom_event_bus ? aws_cloudwatch_event_bus.main[0].arn : "arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:event-bus/default"

  # DLQ ARN to use
  dlq_arn = var.create_dlq ? aws_sqs_queue.dlq[0].arn : var.dlq_arn

  # Use the provided lambda_function_arns map for permissions
  # This is a static map with known keys at plan time
  lambda_permissions = var.lambda_function_arns
}

# ============================================================================
# EventBridge Event Bus
# ============================================================================

resource "aws_cloudwatch_event_bus" "main" {
  count = var.create_custom_event_bus ? 1 : 0
  name  = var.custom_event_bus_name != "" ? var.custom_event_bus_name : "${var.name_prefix}-event-bus"

  tags = merge(var.tags, {
    Name = var.custom_event_bus_name != "" ? var.custom_event_bus_name : "${var.name_prefix}-event-bus"
  })
}

# ============================================================================
# Dynamic EventBridge Rules
# ============================================================================

resource "aws_cloudwatch_event_rule" "rules" {
  for_each = var.rules

  name           = "${var.name_prefix}-${each.key}"
  description    = each.value.description != "" ? each.value.description : "EventBridge rule: ${each.key}"
  event_bus_name = local.event_bus_name

  # Either event pattern or schedule expression must be provided
  event_pattern       = each.value.event_pattern
  schedule_expression = each.value.schedule_expression

  state = each.value.enabled ? "ENABLED" : "DISABLED"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.key}"
  })
}

# ============================================================================
# Dynamic EventBridge Targets
# ============================================================================

resource "aws_cloudwatch_event_target" "targets" {
  for_each = {
    for pair in flatten([
      for rule_key, rule in var.rules : [
        for idx, target in rule.targets : {
          key        = "${rule_key}-${idx}"
          rule_key   = rule_key
          target_idx = idx
          target     = target
        }
      ]
    ]) : pair.key => pair
  }

  rule           = aws_cloudwatch_event_rule.rules[each.value.rule_key].name
  event_bus_name = local.event_bus_name
  arn            = each.value.target.arn
  target_id      = "target-${each.value.target_idx}"

  # Optional: IAM role for target invocation
  role_arn = each.value.target.role_arn

  # Optional: Custom input to target
  input      = each.value.target.input
  input_path = each.value.target.input_path

  # Retry policy
  dynamic "retry_policy" {
    for_each = each.value.target.retry_policy != null ? [each.value.target.retry_policy] : []
    content {
      maximum_event_age_in_seconds = retry_policy.value.maximum_event_age
      maximum_retry_attempts       = retry_policy.value.maximum_retry_attempts
    }
  }

  # Dead letter queue
  dynamic "dead_letter_config" {
    for_each = (each.value.target.dead_letter_arn != null || local.dlq_arn != "") ? [1] : []
    content {
      arn = coalesce(each.value.target.dead_letter_arn, local.dlq_arn)
    }
  }

  depends_on = [aws_cloudwatch_event_rule.rules]
}

# ============================================================================
# Lambda Permissions for EventBridge
# ============================================================================

resource "aws_lambda_permission" "eventbridge" {
  for_each = local.lambda_permissions

  statement_id  = "AllowEventBridgeInvoke-${replace(each.key, "-", "_")}"
  action        = "lambda:InvokeFunction"
  function_name = each.value  # This is the Lambda ARN
  principal     = "events.amazonaws.com"
  source_arn    = local.event_bus_arn

  # Note: This gives permission for any rule on this event bus to invoke the function
  # For more granular control, you could create per-rule permissions
}

# ============================================================================
# Dead Letter Queue (DLQ)
# ============================================================================

resource "aws_sqs_queue" "dlq" {
  count = var.create_dlq ? 1 : 0
  name  = "${var.name_prefix}-eventbridge-dlq"

  message_retention_seconds = var.dlq_message_retention_seconds
  sqs_managed_sse_enabled   = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eventbridge-dlq"
  })
}

resource "aws_sqs_queue_policy" "dlq" {
  count     = var.create_dlq ? 1 : 0
  queue_url = aws_sqs_queue.dlq[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.dlq[0].arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = [
              for rule_key, rule in var.rules :
              "arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:rule/${local.event_bus_name}/${var.name_prefix}-${rule_key}"
            ]
          }
        }
      }
    ]
  })
}

# ============================================================================
# CloudWatch Log Group (Optional)
# ============================================================================

resource "aws_cloudwatch_log_group" "eventbridge" {
  count             = var.enable_eventbridge_logging ? 1 : 0
  name              = "/aws/events/${var.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eventbridge-logs"
  })
}

# ============================================================================
# CloudWatch Alarms
# ============================================================================

# Alarm for failed invocations (monitors all rules)
resource "aws_cloudwatch_metric_alarm" "failed_invocations" {
  for_each = var.enable_cloudwatch_alarms ? var.rules : {}

  alarm_name          = "${var.name_prefix}-${each.key}-failed-invocations"
  alarm_description   = "EventBridge rule ${each.key} has high failed invocation rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FailedInvocations"
  namespace           = "AWS/Events"
  period              = 300
  statistic           = "Sum"
  threshold           = var.failed_invocations_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    RuleName = aws_cloudwatch_event_rule.rules[each.key].name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm for throttled rules (global)
resource "aws_cloudwatch_metric_alarm" "throttled_rules" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-eventbridge-throttled-rules"
  alarm_description   = "EventBridge rules are being throttled"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ThrottledRules"
  namespace           = "AWS/Events"
  period              = 300
  statistic           = "Sum"
  threshold           = var.throttled_rules_threshold
  treat_missing_data  = "notBreaching"

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm for DLQ messages
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  count               = var.create_dlq && var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-eventbridge-dlq-messages"
  alarm_description   = "EventBridge DLQ has messages (failed events)"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.dlq[0].name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}
