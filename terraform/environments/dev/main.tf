# ============================================================
# Dev Environment - main.tf
# Connects all modules together for development environment
# Lowest resource allocation — cost optimised
# Scales to zero when not in use
# ============================================================

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Terraform state stored in GCP — not local machine
  # Allows team to share state safely
  backend "gcs" {
    bucket = "medflow-terraform-state"
    prefix = "environments/dev"
  }
}

# GCP provider — authenticates with GCP
provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Module 1 — Pub/Sub ───────────────────────────────────────
# Create first — storage module needs topic_id from here
module "pubsub" {
  source      = "../../modules/pubsub"
  project_id  = var.project_id
  environment = var.environment
}

# ── Module 2 — Storage ───────────────────────────────────────
# Receives topic_id from pubsub module
# When new PDF arrives — notifies that topic
module "storage" {
  source          = "../../modules/storage"
  project_id      = var.project_id
  region          = var.region
  environment     = var.environment
  pubsub_topic_id = module.pubsub.topic_id
}

# ── Module 3 — BigQuery ──────────────────────────────────────
# Audit logging for all agent decisions
module "bigquery" {
  source      = "../../modules/bigquery"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

# ── Module 4 — Cloud Run ─────────────────────────────────────
# Runs our FastAPI application
# Dev — scales to zero, minimal resources
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
  log_level     = "DEBUG"
}