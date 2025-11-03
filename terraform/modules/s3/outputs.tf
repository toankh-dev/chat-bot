# ============================================================================
# S3 Module Outputs
# ============================================================================

output "bucket_ids" {
  description = "Map of bucket names to IDs"
  value       = { for k, v in aws_s3_bucket.buckets : k => v.id }
}

output "bucket_arns" {
  description = "List of bucket ARNs"
  value       = [for v in aws_s3_bucket.buckets : v.arn]
}

output "bucket_names" {
  description = "Map of bucket keys to bucket names"
  value       = { for k, v in aws_s3_bucket.buckets : k => v.bucket }
}

output "bucket_domain_names" {
  description = "Map of bucket names to domain names"
  value       = { for k, v in aws_s3_bucket.buckets : k => v.bucket_domain_name }
}

output "bucket_regional_domain_names" {
  description = "Map of bucket names to regional domain names"
  value       = { for k, v in aws_s3_bucket.buckets : k => v.bucket_regional_domain_name }
}
