# ============================================================
# Dev Environment - variables.tf
# Input variables for development environment
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
  default     = "dev"
}

variable "min_instances" {
  description = "Minimum Cloud Run instances — 0 scales to zero"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 5
}

variable "memory" {
  description = "Memory per instance"
  type        = string
  default     = "1Gi"
}

variable "cpu" {
  description = "CPU per instance"
  type        = string
  default     = "1"
}

variable "image_tag" {
  description = "Docker image tag — Git commit SHA"
  type        = string
  default     = "latest"
}