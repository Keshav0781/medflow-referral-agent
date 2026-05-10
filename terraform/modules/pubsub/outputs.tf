# ============================================================
# Pub/Sub Module - outputs.tf
# Values exposed to other modules and environments
# ============================================================

output "topic_name" {
  description = "Main Pub/Sub topic name"
  value       = google_pubsub_topic.referral_documents.name
}

output "topic_id" {
  description = "Main Pub/Sub topic ID — used by storage module"
  value       = google_pubsub_topic.referral_documents.id
}

output "subscription_name" {
  description = "Subscription name — used by FastAPI to receive messages"
  value       = google_pubsub_subscription.referral_documents_sub.name
}

output "dead_letter_topic_id" {
  description = "Dead letter topic ID — monitor for failed messages"
  value       = google_pubsub_topic.dead_letter.id
}