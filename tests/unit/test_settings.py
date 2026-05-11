# ============================================================
# Unit Tests — Settings Configuration
# Tests that settings load correctly
# Tests validation of required fields
# Tests default values are correct
# ============================================================

import pytest
import os
from unittest.mock import patch


def test_settings_load_with_valid_env():
    """
    Settings load correctly when all required
    environment variables are present.
    """
    with patch.dict(os.environ, {
        "GCP_PROJECT_ID": "test-project",
        "LANGSMITH_API_KEY": "test-key",
        "ENVIRONMENT": "test"
    }):
        from src.config.settings import Settings
        settings = Settings()
        assert settings.gcp_project_id == "test-project"
        assert settings.langsmith_api_key == "test-key"
        assert settings.environment == "test"


def test_settings_default_values():
    """
    Settings use correct default values
    when optional variables are not set.
    """
    with patch.dict(os.environ, {
        "GCP_PROJECT_ID": "test-project",
        "LANGSMITH_API_KEY": "test-key",
        "ENVIRONMENT": "development",
        "LANGSMITH_TRACING": "true"
    }, clear=False):
        from importlib import reload
        import src.config.settings as settings_module
        reload(settings_module)
        settings = settings_module.Settings()
        assert settings.gcp_region == "europe-west3"
        assert settings.vertex_ai_location == "europe-west3"
        assert settings.vertex_ai_model == "gemini-1.5-pro"
        assert settings.enable_bigquery is False
        assert settings.log_level == "INFO"


def test_routing_confidence_threshold():
    """
    Routing confidence threshold is correctly set.
    Must be 0.70 as defined in requirements.
    """
    with patch.dict(os.environ, {
        "GCP_PROJECT_ID": "test-project",
        "LANGSMITH_API_KEY": "test-key"
    }):
        from src.config.settings import Settings
        settings = Settings()
        assert settings.routing_confidence_threshold == 0.70


def test_routing_accuracy_threshold():
    """
    Routing accuracy threshold is correctly set.
    Must be 0.90 as defined in requirements.
    """
    with patch.dict(os.environ, {
        "GCP_PROJECT_ID": "test-project",
        "LANGSMITH_API_KEY": "test-key"
    }):
        from src.config.settings import Settings
        settings = Settings()
        assert settings.routing_accuracy_threshold == 0.90


def test_urgency_accuracy_threshold():
    """
    Urgency accuracy threshold is correctly set.
    Must be 0.95 as defined in requirements.
    Higher than routing — patient safety requirement.
    """
    with patch.dict(os.environ, {
        "GCP_PROJECT_ID": "test-project",
        "LANGSMITH_API_KEY": "test-key"
    }):
        from src.config.settings import Settings
        settings = Settings()
        assert settings.urgency_accuracy_threshold == 0.95