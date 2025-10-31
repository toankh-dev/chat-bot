# ============================================================================
# DynamoDB Module - NoSQL Database
# ============================================================================

terraform {
  required_version = ">= 1.5.0"
}

# ============================================================================
# DynamoDB Tables
# ============================================================================

resource "aws_dynamodb_table" "tables" {
  for_each = var.tables

  name         = "${var.name_prefix}-${each.key}"
  billing_mode = each.value.billing_mode
  hash_key     = each.value.hash_key
  range_key    = lookup(each.value, "range_key", null)

  # Provisioned capacity (if billing_mode is PROVISIONED)
  read_capacity  = each.value.billing_mode == "PROVISIONED" ? lookup(each.value, "read_capacity", 5) : null
  write_capacity = each.value.billing_mode == "PROVISIONED" ? lookup(each.value, "write_capacity", 5) : null

  # Attributes
  dynamic "attribute" {
    for_each = each.value.attributes

    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  # Global Secondary Indexes
  dynamic "global_secondary_index" {
    for_each = lookup(each.value, "global_secondary_indexes", [])

    content {
      name            = global_secondary_index.value.name
      hash_key        = global_secondary_index.value.hash_key
      range_key       = lookup(global_secondary_index.value, "range_key", null)
      projection_type = global_secondary_index.value.projection_type
      read_capacity   = each.value.billing_mode == "PROVISIONED" ? lookup(global_secondary_index.value, "read_capacity", 5) : null
      write_capacity  = each.value.billing_mode == "PROVISIONED" ? lookup(global_secondary_index.value, "write_capacity", 5) : null

      dynamic "projection" {
        for_each = lookup(global_secondary_index.value, "non_key_attributes", null) != null ? [1] : []

        content {
          non_key_attributes = global_secondary_index.value.non_key_attributes
        }
      }
    }
  }

  # Local Secondary Indexes
  dynamic "local_secondary_index" {
    for_each = lookup(each.value, "local_secondary_indexes", [])

    content {
      name            = local_secondary_index.value.name
      range_key       = local_secondary_index.value.range_key
      projection_type = local_secondary_index.value.projection_type

      dynamic "projection" {
        for_each = lookup(local_secondary_index.value, "non_key_attributes", null) != null ? [1] : []

        content {
          non_key_attributes = local_secondary_index.value.non_key_attributes
        }
      }
    }
  }

  # TTL
  dynamic "ttl" {
    for_each = each.value.ttl_enabled ? [1] : []

    content {
      enabled        = true
      attribute_name = each.value.ttl_attribute
    }
  }

  # Stream
  stream_enabled   = lookup(each.value, "enable_streams", false)
  stream_view_type = lookup(each.value, "enable_streams", false) ? lookup(each.value, "stream_view_type", "NEW_AND_OLD_IMAGES") : null

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  # Deletion protection
  deletion_protection_enabled = var.enable_deletion_protection

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-${each.key}"
      Type = each.key
    }
  )
}

# ============================================================================
# DynamoDB Auto Scaling (Optional, for PROVISIONED billing)
# ============================================================================

resource "aws_appautoscaling_target" "read" {
  for_each = {
    for k, v in var.tables : k => v
    if v.billing_mode == "PROVISIONED" && var.enable_autoscaling
  }

  max_capacity       = var.autoscaling_read_max_capacity
  min_capacity       = var.autoscaling_read_min_capacity
  resource_id        = "table/${aws_dynamodb_table.tables[each.key].name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "read" {
  for_each = {
    for k, v in var.tables : k => v
    if v.billing_mode == "PROVISIONED" && var.enable_autoscaling
  }

  name               = "${var.name_prefix}-${each.key}-read-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.read[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.read[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.read[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
    target_value = var.autoscaling_target_utilization
  }
}

resource "aws_appautoscaling_target" "write" {
  for_each = {
    for k, v in var.tables : k => v
    if v.billing_mode == "PROVISIONED" && var.enable_autoscaling
  }

  max_capacity       = var.autoscaling_write_max_capacity
  min_capacity       = var.autoscaling_write_min_capacity
  resource_id        = "table/${aws_dynamodb_table.tables[each.key].name}"
  scalable_dimension = "dynamodb:table:WriteCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "write" {
  for_each = {
    for k, v in var.tables : k => v
    if v.billing_mode == "PROVISIONED" && var.enable_autoscaling
  }

  name               = "${var.name_prefix}-${each.key}-write-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.write[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.write[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.write[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBWriteCapacityUtilization"
    }
    target_value = var.autoscaling_target_utilization
  }
}

# ============================================================================
# CloudWatch Alarms (Optional)
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "read_throttle" {
  for_each = var.enable_alarms ? var.tables : {}

  alarm_name          = "${var.name_prefix}-${each.key}-read-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ReadThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "DynamoDB read throttle events for ${each.key}"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.tables[each.key].name
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "write_throttle" {
  for_each = var.enable_alarms ? var.tables : {}

  alarm_name          = "${var.name_prefix}-${each.key}-write-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "WriteThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "DynamoDB write throttle events for ${each.key}"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.tables[each.key].name
  }

  tags = var.tags
}
