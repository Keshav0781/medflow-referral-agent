# ============================================================
# BigQuery Module - main.tf
# Creates dataset and table for audit logging
# Every agent decision logged here permanently
# Healthcare compliance — 7 year retention
# ============================================================

# ── Dataset ─────────────────────────────────────────────────
# Like a database — contains all our tables
resource "google_bigquery_dataset" "medflow_logs" {
  dataset_id  = "medflow_logs_${var.environment}"
  description = "Audit logs for MedFlow Referral Agent - ${var.environment}"
  location    = var.region
  project     = var.project_id

  # Never accidentally delete data
  delete_contents_on_destroy = false
}

# ── Table ────────────────────────────────────────────────────
# One row written per processed referral document
resource "google_bigquery_table" "referral_logs" {
  dataset_id = google_bigquery_dataset.medflow_logs.dataset_id
  table_id   = "referral_processing_logs"
  project    = var.project_id

  # Prevent accidental table deletion in production
  deletion_protection = true

  # Partition by day — faster and cheaper queries
  # "Show me last week's data" only scans last week
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  # Cluster by frequently filtered columns
  # Makes queries like "show all Emergency cases" faster
  clustering = ["department", "urgency", "environment"]

  # Schema — defines every column name and type
  schema = jsonencode([
    {
      name        = "timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "When the document was processed"
    },
    {
      name        = "document_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Unique referral document identifier"
    },
    {
      name        = "session_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Agent processing session ID"
    },
    {
      name        = "department"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Department the referral was routed to"
    },
    {
      name        = "routing_confidence"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "AI confidence score for routing decision"
    },
    {
      name        = "routing_reason"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "AI reasoning for routing decision"
    },
    {
      name        = "urgency"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Urgency classification — Routine, Semi-urgent, Emergency"
    },
    {
      name        = "urgency_confidence"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "AI confidence score for urgency classification"
    },
    {
      name        = "urgency_reason"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "AI reasoning for urgency classification"
    },
    {
      name        = "processing_time_seconds"
      type        = "FLOAT"
      mode        = "NULLABLE"
      description = "Total time to process document in seconds"
    },
    {
      name        = "coordinator_action"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "What coordinator did — approved, edited, rejected"
    },
    {
      name        = "escalation_triggered"
      type        = "BOOLEAN"
      mode        = "NULLABLE"
      description = "Whether Emergency escalation was triggered"
    },
    {
      name        = "langsmith_trace_id"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "LangSmith trace ID for debugging"
    },
    {
      name        = "summary"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "AI generated summary of the referral for the receiving department"
    },
    {
      name        = "environment"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Which environment processed this — dev, staging, prod"
    }
  ])
}