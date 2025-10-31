# ============================================================================
# DynamoDB Module Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for table names"
  type        = string
}

variable "tables" {
  description = "Map of DynamoDB table configurations"
  type        = any
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for all tables"
  type        = bool
  default     = true
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for all tables"
  type        = bool
  default     = false
}

variable "enable_autoscaling" {
  description = "Enable autoscaling for provisioned tables"
  type        = bool
  default     = false
}

variable "autoscaling_read_min_capacity" {
  description = "Minimum read capacity for autoscaling"
  type        = number
  default     = 5
}

variable "autoscaling_read_max_capacity" {
  description = "Maximum read capacity for autoscaling"
  type        = number
  default     = 100
}

variable "autoscaling_write_min_capacity" {
  description = "Minimum write capacity for autoscaling"
  type        = number
  default     = 5
}

variable "autoscaling_write_max_capacity" {
  description = "Maximum write capacity for autoscaling"
  type        = number
  default     = 100
}

variable "autoscaling_target_utilization" {
  description = "Target utilization percentage for autoscaling"
  type        = number
  default     = 70
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms for throttling"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
