"""
Application settings for MedFlow Referral Agent.
Reads all configuration from environment variables.
Fails fast if any required variable is missing.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    All application settings loaded from environment variables.
    Required variables must be set — application will not start
    without them.
    """

    # ── Google Cloud Platform ──────────────────────────────
    gcp_project_id: str = Field(
        ...,
        description="GCP project ID"
    )
    gcp_region: str = Field(
        default="europe-west3",
        description="GCP region"
    )

    # ── Vertex AI ──────────────────────────────────────────
    vertex_ai_location: str = Field(
        default="europe-west3",
        description="Vertex AI location"
    )
    vertex_ai_model: str = Field(
        default="gemini-2.5-flash",
        description="Vertex AI model name"
    )

    # ── LangSmith Observability ────────────────────────────
    langsmith_api_key: str = Field(
        ...,
        description="LangSmith API key for tracing"
    )
    langsmith_project: str = Field(
        default="medflow-referral-agent",
        description="LangSmith project name"
    )
    langsmith_tracing: bool = Field(
        default=True,
        description="Enable LangSmith tracing"
    )

    # ── ChromaDB ───────────────────────────────────────────
    chroma_persist_dir: str = Field(
        default="./data/chroma",
        description="ChromaDB persistence directory"
    )

    # ── BigQuery Audit Logging ─────────────────────────────
    bigquery_dataset: str = Field(
        default="medflow_logs",
        description="BigQuery dataset name"
    )
    bigquery_table: str = Field(
        default="referral_processing_logs",
        description="BigQuery table name"
    )
    enable_bigquery: bool = Field(
        default=False,
        description="Enable BigQuery audit logging"
    )

    # ── Application Settings ───────────────────────────────
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )

    # ── Routing Thresholds ─────────────────────────────────
    routing_confidence_threshold: float = Field(
        default=0.70,
        description="Minimum confidence for routing decision"
    )
    routing_accuracy_threshold: float = Field(
        default=0.90,
        description="Minimum routing accuracy for deployment"
    )
    urgency_accuracy_threshold: float = Field(
        default=0.95,
        description="Minimum urgency accuracy for deployment"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Settings are loaded once and reused across the application.
    Cache is cleared between tests.
    """
    return Settings()