# ============================================================
# Pub/Sub Module - variables.tf
# Defines all inputs this module accepts
# ============================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name — dev, staging, or prod"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west3"
}

variable "message_retention_seconds" {
  description = "How long to retain undelivered messages"
  type        = number
  default     = 86400
}

variable "ack_deadline_seconds" {
  description = "Time to process message before redelivery"
  type        = number
  default     = 300
}

variable "max_delivery_attempts" {
  description = "Max attempts before sending to dead letter"
  type        = number
  default     = 5
}
variable "push_endpoint" {
  description = "Cloud Run webhook URL for push subscription — empty string means pull subscription"
  type        = string
  default     = ""
}
