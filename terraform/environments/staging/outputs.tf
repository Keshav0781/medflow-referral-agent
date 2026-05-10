# ============================================================
# Staging Environment - outputs.tf
# Values displayed after terraform apply completes
# ============================================================

output "cloud_run_url" {
  description = "Staging Cloud Run URL — Anna reviews here before prod"
  value       = module.cloud_run.service_url
}

output "bucket_name" {
  description = "Staging storage bucket — anonymised test documents"
  value       = module.storage.bucket_name
}

output "pubsub_topic" {
  description = "Staging Pub/Sub topic name"
  value       = module.pubsub.topic_name
}

output "bigquery_dataset" {
  description = "Staging BigQuery dataset — evaluation results stored here"
  value       = module.bigquery.dataset_id
}