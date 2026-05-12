# ============================================================
# Staging Environment - main.tf
# Mirrors production as closely as possible
# Used for final testing before production deployment
# Ragas evaluation runs here before any prod deployment
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
    prefix = "environments/staging"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Module 1 — Pub/Sub ───────────────────────────────────────
module "pubsub" {
  source        = "../../modules/pubsub"
  project_id    = var.project_id
  environment   = var.environment
  push_endpoint = "${module.cloud_run.service_url}/webhook/pubsub"
  depends_on    = [module.cloud_run]
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
module "bigquery" {
  source      = "../../modules/bigquery"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

# ── Module 4 — Cloud Run ─────────────────────────────────────
# Staging — more resources than dev
# Mirrors production sizing as closely as possible
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