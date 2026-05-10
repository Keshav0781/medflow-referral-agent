# ============================================================
# BigQuery Module - variables.tf
# Defines all inputs this module accepts
# ============================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for BigQuery dataset"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "Environment name — dev, staging, or prod"
  type        = string
}

variable "retention_days" {
  description = "How many days to retain audit log data"
  type        = number
  default     = 2555
}