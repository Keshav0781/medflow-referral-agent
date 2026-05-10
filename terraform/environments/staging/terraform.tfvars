# ============================================================
# Staging Environment - terraform.tfvars
# Actual values for staging environment
# More resources than dev — mirrors production closely
# ============================================================

project_id    = "medflow-referral-agent"
region        = "europe-west3"
environment   = "staging"
min_instances = 0
max_instances = 8
memory        = "2Gi"
cpu           = "2"
image_tag     = "latest"