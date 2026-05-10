# ============================================================
# Storage Module - variables.tf
# Defines all inputs this module accepts
# ============================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for storage bucket"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "Environment name — dev, staging, or prod"
  type        = string
}

variable "pubsub_topic_id" {
  description = "Pub/Sub topic ID to notify when new file arrives"
  type        = string
}

variable "retention_days" {
  description = "How many days to keep referral documents"
  type        = number
  default     = 365
}