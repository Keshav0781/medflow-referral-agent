# ============================================================
# Dev Environment - terraform.tfvars
# Actual values for development environment
# This file fills in the variables defined in variables.tf
# ============================================================

project_id    = "medflow-referral-agent"
region        = "europe-west3"
environment   = "dev"
min_instances = 0
max_instances = 5
memory        = "1Gi"
cpu           = "1"
image_tag     = "latest"