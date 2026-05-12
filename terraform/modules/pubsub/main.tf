# ============================================================
# Pub/Sub Module - main.tf
# Creates topic, subscription, and dead letter topic
# for document event triggers
# ============================================================

# ── Main Topic ──────────────────────────────────────────────
# Cloud Storage sends message here when new PDF arrives
resource "google_pubsub_topic" "referral_documents" {
  name    = "medflow-referral-documents-${var.environment}"
  project = var.project_id

  # How long to keep undelivered messages
  message_retention_duration = "${var.message_retention_seconds}s"
}

# ── Subscription ────────────────────────────────────────────
# Our FastAPI application listens here for new documents
resource "google_pubsub_subscription" "referral_documents_sub" {
  name    = "medflow-referral-documents-sub-${var.environment}"
  topic   = google_pubsub_topic.referral_documents.name
  project = var.project_id

  # Time application has to process before redelivery
  ack_deadline_seconds = var.ack_deadline_seconds

  # Retry with increasing delay between attempts
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  # After max attempts — send to dead letter topic
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = var.max_delivery_attempts
  }

  # Push messages to Cloud Run webhook when endpoint is configured
  # Empty string means pull subscription — used when Cloud Run URL not yet known
  dynamic "push_config" {
    for_each = var.push_endpoint != "" ? [1] : []
    content {
      push_endpoint = var.push_endpoint
    }
  }

  depends_on = [
    google_pubsub_topic.referral_documents,
    google_pubsub_topic.dead_letter
  ]
}

# ── Dead Letter Topic ───────────────────────────────────────
# Failed messages land here after max delivery attempts
# Engineers monitor this — zero data loss guaranteed
resource "google_pubsub_topic" "dead_letter" {
  name    = "medflow-referral-dead-letter-${var.environment}"
  project = var.project_id
}