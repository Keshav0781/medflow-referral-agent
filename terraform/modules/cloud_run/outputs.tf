# ============================================================
# Cloud Run Module - outputs.tf
# Values this module exposes to other modules and environments
# ============================================================

output "service_url" {
  description = "Public URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.medflow_agent.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.medflow_agent.name
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.cloud_run_sa.email
}