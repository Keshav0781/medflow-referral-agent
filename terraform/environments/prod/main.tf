# ============================================================
# Production Environment - main.tf
# Live system — real hospital data — real patients
# Manual approval required before any deployment
# Maximum resources — always warm — zero cold starts
# ============================================================

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "medflow-terraform-state"
    prefix = "environments/prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Module 1 — Pub/Sub ───────────────────────────────────────
module "pubsub" {
  source      = "../../modules/pubsub"
  project_id  = var.project_id
  environment = var.environment
}

# ── Module 2 — Storage ───────────────────────────────────────
module "storage" {
  source          = "../../modules/storage"
  project_id      = var.project_id
  region          = var.region
  environment     = var.environment
  pubsub_topic_id = module.pubsub.topic_id
}

# ── Module 3 — BigQuery ──────────────────────────────────────
# 7 year retention — healthcare compliance requirement
module "bigquery" {
  source         = "../../modules/bigquery"
  project_id     = var.project_id
  region         = var.region
  environment    = var.environment
  retention_days = 2555
}

# ── Module 4 — Cloud Run ─────────────────────────────────────
# Production — maximum resources
# Always warm — min_instances = 1
# Never scale to zero — hospital cannot wait for cold start
module "cloud_run" {
  source        = "../../modules/cloud_run"
  project_id    = var.project_id
  region        = var.region
  environment   = var.environment
  min_instances = var.min_instances
  max_instances = var.max_instances
  memory        = var.memory
  cpu           = var.cpu
  image_tag     = var.image_tag
  log_level     = "INFO"
}