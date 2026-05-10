# ============================================================
# Staging Environment - variables.tf
# Input variables for staging environment
# ============================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "min_instances" {
  description = "Minimum Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 8
}

variable "memory" {
  description = "Memory per instance"
  type        = string
  default     = "2Gi"
}

variable "cpu" {
  description = "CPU per instance"
  type        = string
  default     = "2"
}

variable "image_tag" {
  description = "Docker image tag — Git commit SHA"
  type        = string
  default     = "latest"
}