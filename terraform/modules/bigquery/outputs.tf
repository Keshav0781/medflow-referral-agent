# ============================================================
# BigQuery Module - outputs.tf
# Values exposed to other modules and environments
# ============================================================

output "dataset_id" {
  description = "BigQuery dataset ID — used by application to write logs"
  value       = google_bigquery_dataset.medflow_logs.dataset_id
}

output "table_id" {
  description = "BigQuery table ID — used by application to write rows"
  value       = google_bigquery_table.referral_logs.table_id
}

output "dataset_location" {
  description = "Dataset location — confirms EU data residency"
  value       = google_bigquery_dataset.medflow_logs.location
}