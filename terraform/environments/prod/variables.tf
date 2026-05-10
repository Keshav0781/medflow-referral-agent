# ============================================================
# Production Environment - variables.tf
# Input variables for production environment
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
  default     = "prod"
}

variable "min_instances" {
  description = "Minimum Cloud Run instances — always 1 in prod"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 20
}

variable "memory" {
  description = "Memory per instance"
  type        = string
  default     = "4Gi"
}

variable "cpu" {
  description = "CPU per instance"
  type        = string
  default     = "2"
}

variable "image_tag" {
  description = "Docker image tag — always Git commit SHA in prod"
  type        = string
}