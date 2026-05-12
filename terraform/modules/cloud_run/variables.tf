# ============================================================
# Cloud Run Module - variables.tf
# Defines all inputs this module accepts
# Each environment passes different values
# ============================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region where Cloud Run deploys"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "Environment name — dev, staging, or prod"
  type        = string
}

variable "min_instances" {
  description = "Minimum Cloud Run instances — 0 for dev, 1 for prod"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum Cloud Run instances for scaling"
  type        = number
  default     = 10
}

variable "memory" {
  description = "Memory per instance — 1Gi for dev, 4Gi for prod"
  type        = string
  default     = "2Gi"
}

variable "cpu" {
  description = "CPU per instance"
  type        = string
  default     = "2"
}

variable "timeout_seconds" {
  description = "Request timeout — 300s for document processing"
  type        = number
  default     = 300
}

variable "artifact_repo" {
  description = "Artifact Registry repository name"
  type        = string
  default     = "medflow-repo"
}

variable "image_name" {
  description = "Docker image name"
  type        = string
  default     = "medflow-agent"
}

variable "image_tag" {
  description = "Docker image tag — always Git commit SHA in production"
  type        = string
  default     = "latest"
}

variable "log_level" {
  description = "Application log level — DEBUG for dev, INFO for prod"
  type        = string
  default     = "INFO"
}
variable "github_actions_sa" {
  description = "GitHub Actions deployer service account email — granted actAs permission on Cloud Run SA"
  type        = string
  default     = "github-actions-deployer@medflow-referral-agent.iam.gserviceaccount.com"
}
