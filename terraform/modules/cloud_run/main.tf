# ============================================================
# Cloud Run Module - main.tf
# Creates Cloud Run service for MedFlow Referral Agent
# Uses variables defined in variables.tf
# ============================================================

# ── Cloud Run Service ───────────────────────────────────────
resource "google_cloud_run_v2_service" "medflow_agent" {
  name     = "medflow-referral-agent-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    # Identity our application uses to access GCP
    service_account = google_service_account.cloud_run_sa.email

    # Scaling — dev scales to zero, prod always warm
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      # Docker image tagged with Git commit SHA
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo}/${var.image_name}:${var.image_tag}"

      # Memory and CPU limits
      resources {
        limits = {
          memory = var.memory
          cpu    = var.cpu
        }
      }

      # ── Secrets from Secret Manager ──────────────────────
      # Application never sees raw secret values in code
      # GCP fetches them securely at runtime

      env {
        name = "GCP_PROJECT_ID"
        value_source {
          secret_key_ref {
            secret  = "GCP-PROJECT-ID"
            version = "latest"
          }
        }
      }

      env {
        name = "LANGSMITH_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "LANGSMITH-API-KEY"
            version = "latest"
          }
        }
      }

      env {
        name = "LANGSMITH_PROJECT"
        value_source {
          secret_key_ref {
            secret  = "LANGSMITH-PROJECT"
            version = "latest"
          }
        }
      }

      env {
        name = "BIGQUERY_DATASET"
        value_source {
          secret_key_ref {
            secret  = "BIGQUERY-DATASET"
            version = "latest"
          }
        }
      }

      env {
        name = "BIGQUERY_TABLE"
        value_source {
          secret_key_ref {
            secret  = "BIGQUERY-TABLE"
            version = "latest"
          }
        }
      }

      env {
        name = "ENVIRONMENT"
        value_source {
          secret_key_ref {
            secret  = "ENVIRONMENT"
            version = "latest"
          }
        }
      }

      # ── Non-secret environment variables ─────────────────
      env {
        name  = "GCP_REGION"
        value = var.region
      }

      env {
        name  = "VERTEX_AI_LOCATION"
        value = var.region
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      ports {
        container_port = 8080
      }
    }

    timeout = "${var.timeout_seconds}s"
  }

  # Always send traffic to latest revision
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  # Wait for service account and permissions before creating
  depends_on = [
    google_service_account.cloud_run_sa,
    google_project_iam_member.secret_accessor,
    google_project_iam_member.vertex_ai_user,
    google_project_iam_member.bigquery_editor,
    google_project_iam_member.storage_object_viewer,
  ]

  # CI/CD pipeline owns the image tag — Terraform must not override it
  # Every pipeline deployment uses a specific commit SHA
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}

# ── Service Account ─────────────────────────────────────────
# Identity our application uses to access GCP services
resource "google_service_account" "cloud_run_sa" {
  account_id   = "medflow-agent-${var.environment}"
  display_name = "MedFlow Agent - ${var.environment}"
  project      = var.project_id
}

# ── IAM Permissions ─────────────────────────────────────────
# Principle of least privilege — only minimum needed

# Read secrets from Secret Manager
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Call Vertex AI language models
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Write audit logs to BigQuery
resource "google_project_iam_member" "bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Read referral PDFs from Cloud Storage
resource "google_project_iam_member" "storage_object_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Receive Pub/Sub messages when new document arrives
resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}
# Allow public access to Cloud Run service
# Required for health checks and coordinator dashboard
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.medflow_agent.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow github-actions-deployer to deploy as Cloud Run service account
# Required for CI/CD pipeline to deploy new revisions
resource "google_service_account_iam_member" "github_actions_sa_user" {
  service_account_id = google_service_account.cloud_run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${var.github_actions_sa}"
}
