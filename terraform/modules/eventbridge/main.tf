# EventBridge Module for KASS Chatbot
# Creates EventBridge rules for async processing

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Data source for current AWS region
data "aws_region" "current" {}

# ============================================================================
# EventBridge Event Bus
# ============================================================================

resource "aws_cloudwatch_event_bus" "main" {
  count = var.create_custom_event_bus ? 1 : 0
  name  = "${var.name_prefix}-event-bus"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-event-bus"
  })
}

# Use custom event bus or default
locals {
  event_bus_name = var.create_custom_event_bus ? aws_cloudwatch_event_bus.main[0].name : "default"
  event_bus_arn  = var.create_custom_event_bus ? aws_cloudwatch_event_bus.main[0].arn : "arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:event-bus/default"
}

# ============================================================================
# EventBridge Rules
# ============================================================================

# Rule: Document uploaded to S3 (triggers document processor)
resource "aws_cloudwatch_event_rule" "document_uploaded" {
  name           = "${var.name_prefix}-document-uploaded"
  description    = "Trigger document processor when document is uploaded to S3"
  event_bus_name = local.event_bus_name

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [var.documents_bucket_name]
      }
    }
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-document-uploaded"
  })
}

# Target: Lambda function for document processor
resource "aws_cloudwatch_event_target" "document_processor" {
  rule           = aws_cloudwatch_event_rule.document_uploaded.name
  event_bus_name = local.event_bus_name
  arn            = var.document_processor_lambda_arn
  target_id      = "DocumentProcessor"

  # Retry policy
  retry_policy {
    maximum_retry_attempts       = 3
    maximum_event_age_in_seconds = 3600
  }

  # Dead letter queue
  dead_letter_config {
    arn = var.dlq_arn != "" ? var.dlq_arn : null
  }
}

# Rule: Scheduled data fetching (runs daily)
resource "aws_cloudwatch_event_rule" "scheduled_data_fetch" {
  count          = var.enable_scheduled_fetch ? 1 : 0
  name           = "${var.name_prefix}-scheduled-data-fetch"
  description    = "Trigger data fetcher on a schedule"
  event_bus_name = local.event_bus_name
  schedule_expression = var.fetch_schedule

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-scheduled-data-fetch"
  })
}

# Target: Lambda function for data fetcher
resource "aws_cloudwatch_event_target" "data_fetcher" {
  count          = var.enable_scheduled_fetch ? 1 : 0
  rule           = aws_cloudwatch_event_rule.scheduled_data_fetch[0].name
  event_bus_name = local.event_bus_name
  arn            = var.data_fetcher_lambda_arn
  target_id      = "DataFetcher"

  # Input to Lambda
  input = jsonencode({
    source = "eventbridge"
    action = "fetch_data"
  })

  # Retry policy
  retry_policy {
    maximum_retry_attempts       = 2
    maximum_event_age_in_seconds = 1800
  }

  # Dead letter queue
  dead_letter_config {
    arn = var.dlq_arn != "" ? var.dlq_arn : null
  }
}

# Rule: Scheduled Discord fetching (runs every hour)
resource "aws_cloudwatch_event_rule" "scheduled_discord_fetch" {
  count          = var.enable_discord_fetch ? 1 : 0
  name           = "${var.name_prefix}-scheduled-discord-fetch"
  description    = "Trigger Discord fetcher on a schedule"
  event_bus_name = local.event_bus_name
  schedule_expression = var.discord_fetch_schedule

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-scheduled-discord-fetch"
  })
}

# Target: Lambda function for Discord fetcher
resource "aws_cloudwatch_event_target" "discord_fetcher" {
  count          = var.enable_discord_fetch ? 1 : 0
  rule           = aws_cloudwatch_event_rule.scheduled_discord_fetch[0].name
  event_bus_name = local.event_bus_name
  arn            = var.discord_handler_lambda_arn
  target_id      = "DiscordFetcher"

  # Input to Lambda
  input = jsonencode({
    source = "eventbridge"
    action = "fetch_messages"
  })

  # Retry policy
  retry_policy {
    maximum_retry_attempts       = 2
    maximum_event_age_in_seconds = 1800
  }

  # Dead letter queue
  dead_letter_config {
    arn = var.dlq_arn != "" ? var.dlq_arn : null
  }
}

# Rule: Async report generation
resource "aws_cloudwatch_event_rule" "report_generation" {
  count          = var.enable_report_generation ? 1 : 0
  name           = "${var.name_prefix}-report-generation"
  description    = "Trigger report generation for async requests"
  event_bus_name = local.event_bus_name

  event_pattern = jsonencode({
    source      = ["kass.chatbot"]
    detail-type = ["Report Requested"]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-report-generation"
  })
}

# Target: Lambda function for report generation
resource "aws_cloudwatch_event_target" "report_generator" {
  count          = var.enable_report_generation ? 1 : 0
  rule           = aws_cloudwatch_event_rule.report_generation[0].name
  event_bus_name = local.event_bus_name
  arn            = var.report_tool_lambda_arn
  target_id      = "ReportGenerator"

  # Retry policy
  retry_policy {
    maximum_retry_attempts       = 2
    maximum_event_age_in_seconds = 7200
  }

  # Dead letter queue
  dead_letter_config {
    arn = var.dlq_arn != "" ? var.dlq_arn : null
  }
}

# Rule: Cache warming (optional - runs every 5 minutes)
resource "aws_cloudwatch_event_rule" "cache_warming" {
  count          = var.enable_cache_warming ? 1 : 0
  name           = "${var.name_prefix}-cache-warming"
  description    = "Warm up Lambda functions to reduce cold starts"
  event_bus_name = local.event_bus_name
  schedule_expression = "rate(5 minutes)"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cache-warming"
  })
}

# Target: Orchestrator Lambda for cache warming
resource "aws_cloudwatch_event_target" "cache_warmer_orchestrator" {
  count          = var.enable_cache_warming ? 1 : 0
  rule           = aws_cloudwatch_event_rule.cache_warming[0].name
  event_bus_name = local.event_bus_name
  arn            = var.orchestrator_lambda_arn
  target_id      = "CacheWarmerOrchestrator"

  # Input to Lambda (health check)
  input = jsonencode({
    source = "eventbridge"
    action = "health_check"
  })
}

# Target: Vector search Lambda for cache warming
resource "aws_cloudwatch_event_target" "cache_warmer_search" {
  count          = var.enable_cache_warming ? 1 : 0
  rule           = aws_cloudwatch_event_rule.cache_warming[0].name
  event_bus_name = local.event_bus_name
  arn            = var.vector_search_lambda_arn
  target_id      = "CacheWarmerSearch"

  # Input to Lambda (health check)
  input = jsonencode({
    source = "eventbridge"
    action = "health_check"
  })
}

# ============================================================================
# Dead Letter Queue (DLQ) for failed events
# ============================================================================

resource "aws_sqs_queue" "dlq" {
  count = var.create_dlq ? 1 : 0
  name  = "${var.name_prefix}-eventbridge-dlq"

  # Message retention (14 days)
  message_retention_seconds = 1209600

  # Enable encryption
  sqs_managed_sse_enabled = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eventbridge-dlq"
  })
}

# DLQ policy to allow EventBridge to send messages
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
      }
    ]
  })
}

# ============================================================================
# CloudWatch Alarms for EventBridge
# ============================================================================

# Alarm for failed invocations
resource "aws_cloudwatch_metric_alarm" "failed_invocations" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-eventbridge-failed-invocations"
  alarm_description   = "EventBridge has high failed invocation rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FailedInvocations"
  namespace           = "AWS/Events"
  period              = 300
  statistic           = "Sum"
  threshold           = var.failed_invocations_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    RuleName = aws_cloudwatch_event_rule.document_uploaded.name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm for throttled rules
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

# ============================================================================
# CloudWatch Log Group for EventBridge (optional)
# ============================================================================

resource "aws_cloudwatch_log_group" "eventbridge" {
  count             = var.enable_eventbridge_logging ? 1 : 0
  name              = "/aws/events/${var.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eventbridge-logs"
  })
}
