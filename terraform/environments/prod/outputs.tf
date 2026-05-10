# ============================================================
# Production Environment - outputs.tf
# Values displayed after terraform apply completes
# ============================================================

output "cloud_run_url" {
  description = "Production Cloud Run URL — live system for hospitals"
  value       = module.cloud_run.service_url
}

output "bucket_name" {
  description = "Production storage bucket — real patient referral documents"
  value       = module.storage.bucket_name
}

output "pubsub_topic" {
  description = "Production Pub/Sub topic name"
  value       = module.pubsub.topic_name
}

output "bigquery_dataset" {
  description = "Production BigQuery dataset — 7 year compliance logs"
  value       = module.bigquery.dataset_id
}

output "service_account" {
  description = "Production service account — monitor access carefully"
  value       = module.cloud_run.service_account_email
}