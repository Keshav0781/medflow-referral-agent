# ============================================================
# Production Environment - terraform.tfvars
# Actual values for production environment
# Maximum resources — always warm — real hospital data
# ============================================================

project_id    = "medflow-referral-agent"
region        = "europe-west3"
environment   = "prod"
min_instances = 1
max_instances = 20
memory        = "4Gi"
cpu           = "2"

# image_tag intentionally not set here
# Must be provided explicitly during deployment
# via CI/CD pipeline with exact Git commit SHA
# Example: terraform apply -var="image_tag=ac27c6f"