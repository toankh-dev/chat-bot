# ============================================================================
# S3 Module - Object Storage
# ============================================================================

terraform {
  required_version = ">= 1.5.0"
}

# ============================================================================
# S3 Buckets
# ============================================================================

resource "aws_s3_bucket" "buckets" {
  for_each = var.buckets

  bucket = "${var.name_prefix}-${each.key}"

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-${each.key}"
      Type = each.key
    }
  )
}

# ============================================================================
# Bucket Versioning
# ============================================================================

resource "aws_s3_bucket_versioning" "buckets" {
  for_each = var.buckets

  bucket = aws_s3_bucket.buckets[each.key].id

  versioning_configuration {
    status = each.value.versioning_enabled ? "Enabled" : "Disabled"
  }
}

# ============================================================================
# Bucket Encryption
# ============================================================================

resource "aws_s3_bucket_server_side_encryption_configuration" "buckets" {
  for_each = var.buckets

  bucket = aws_s3_bucket.buckets[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# ============================================================================
# Block Public Access
# ============================================================================

resource "aws_s3_bucket_public_access_block" "buckets" {
  for_each = var.buckets

  bucket = aws_s3_bucket.buckets[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# Lifecycle Rules
# ============================================================================

resource "aws_s3_bucket_lifecycle_configuration" "buckets" {
  for_each = {
    for k, v in var.buckets : k => v
    if length(v.lifecycle_rules) > 0
  }

  bucket = aws_s3_bucket.buckets[each.key].id

  dynamic "rule" {
    for_each = each.value.lifecycle_rules

    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      # Transitions
      dynamic "transition" {
        for_each = lookup(rule.value, "transitions", [])

        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      # Expiration
      dynamic "expiration" {
        for_each = lookup(rule.value, "expiration", null) != null ? [rule.value.expiration] : []

        content {
          days = expiration.value.days
        }
      }

      # Filter (optional)
      dynamic "filter" {
        for_each = lookup(rule.value, "prefix", null) != null ? [1] : []

        content {
          prefix = lookup(rule.value, "prefix", "")
        }
      }
    }
  }

  depends_on = [aws_s3_bucket_versioning.buckets]
}

# ============================================================================
# Event Notifications
# ============================================================================

resource "aws_s3_bucket_notification" "lambda" {
  count = var.enable_event_notifications && var.lambda_processor_arn != null ? 1 : 0

  bucket = aws_s3_bucket.buckets["documents"].id

  lambda_function {
    lambda_function_arn = var.lambda_processor_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = ""
    filter_suffix       = ""
  }

  depends_on = [aws_lambda_permission.allow_s3[0]]
}

# Lambda permission for S3 to invoke
resource "aws_lambda_permission" "allow_s3" {
  count = var.enable_event_notifications && var.lambda_processor_arn != null ? 1 : 0

  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_processor_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.buckets["documents"].arn
}

# ============================================================================
# Bucket Policies
# ============================================================================

# Documents bucket policy - Enforce encryption
resource "aws_s3_bucket_policy" "documents" {
  bucket = aws_s3_bucket.buckets["documents"].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.buckets["documents"].arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      }
    ]
  })
}

# Logs bucket policy - Allow log delivery
resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.buckets["logs"].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSLogDeliveryWrite"
        Effect = "Allow"
        Principal = {
          Service = "logging.s3.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.buckets["logs"].arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Sid    = "AWSLogDeliveryAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "logging.s3.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.buckets["logs"].arn
      }
    ]
  })
}

# ============================================================================
# CORS Configuration (Optional)
# ============================================================================

resource "aws_s3_bucket_cors_configuration" "documents" {
  count = var.enable_cors ? 1 : 0

  bucket = aws_s3_bucket.buckets["documents"].id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = var.cors_allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# ============================================================================
# Bucket Metrics (Optional)
# ============================================================================

resource "aws_s3_bucket_metric" "documents" {
  count = var.enable_metrics ? 1 : 0

  bucket = aws_s3_bucket.buckets["documents"].id
  name   = "EntireBucket"
}

# ============================================================================
# Intelligent Tiering Configuration (Optional)
# ============================================================================

resource "aws_s3_bucket_intelligent_tiering_configuration" "documents" {
  count = var.enable_intelligent_tiering ? 1 : 0

  bucket = aws_s3_bucket.buckets["documents"].id
  name   = "EntireBucket"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}
