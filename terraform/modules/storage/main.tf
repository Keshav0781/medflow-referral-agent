# ============================================================
# Storage Module - main.tf
# Creates Cloud Storage bucket for referral PDF documents
# Automatically notifies Pub/Sub when new file arrives
# ============================================================

# ── Storage Bucket ───────────────────────────────────────────
# Secure file cabinet for referral PDF documents
resource "google_storage_bucket" "referral_documents" {
  name          = "medflow-referral-docs-${var.environment}-${var.project_id}"
  location      = var.region
  project       = var.project_id

  # Only delete bucket if it is empty
  # Prevents accidental data loss
  force_destroy = false

  # Uniform access — no per-file permissions
  # All access controlled at bucket level
  uniform_bucket_level_access = true

  # Keep previous versions of files
  # If file is accidentally overwritten — can recover
  versioning {
    enabled = true
  }

  # Automatically delete files after retention period
  lifecycle_rule {
    condition {
      age = var.retention_days
    }
    action {
      type = "Delete"
    }
  }

  # Block all public access — patient data is private
  public_access_prevention = "enforced"
}

# ── Pub/Sub Notification ─────────────────────────────────────
# When new PDF arrives — automatically notify Pub/Sub
# This triggers our agent to start processing
resource "google_storage_notification" "referral_notification" {
  bucket         = google_storage_bucket.referral_documents.name
  payload_format = "JSON_API_V1"
  topic          = var.pubsub_topic_id
  event_types    = ["OBJECT_FINALIZE"]

  depends_on = [
    google_storage_bucket.referral_documents
  ]
}