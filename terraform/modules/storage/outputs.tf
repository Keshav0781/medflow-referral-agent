# ============================================================
# Storage Module - outputs.tf
# Values exposed to other modules and environments
# ============================================================

output "bucket_name" {
  description = "Cloud Storage bucket name — used by application to upload files"
  value       = google_storage_bucket.referral_documents.name
}

output "bucket_url" {
  description = "Cloud Storage bucket URL — full GCS path"
  value       = google_storage_bucket.referral_documents.url
}

output "bucket_location" {
  description = "Bucket location — confirms EU data residency"
  value       = google_storage_bucket.referral_documents.location
}