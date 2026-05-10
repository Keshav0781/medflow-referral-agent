# ============================================================
# Dev Environment - outputs.tf
# Values displayed after terraform apply completes
# Useful for verifying what was created
# ============================================================

output "cloud_run_url" {
  description = "Dev Cloud Run service URL — use this to test the application"
  value       = module.cloud_run.service_url
}

output "bucket_name" {
  description = "Dev storage bucket name — upload test documents here"
  value       = module.storage.bucket_name
}

output "pubsub_topic" {
  description = "Dev Pub/Sub topic name — verify events are flowing"
  value       = module.pubsub.topic_name
}

output "bigquery_dataset" {
  description = "Dev BigQuery dataset — query audit logs here"
  value       = module.bigquery.dataset_id
}