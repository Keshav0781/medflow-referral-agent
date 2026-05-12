# ============================================================
# Integration Tests — FastAPI Application
# Tests all API endpoints using FastAPI test client
# Does not require GCP, Vertex AI, or ChromaDB
# Tests the API layer in isolation
# ============================================================

import base64
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.api.main import app

client = TestClient(app)


# ── Health Check Tests ────────────────────────────────────────

def test_health_check_returns_200():
    """Health endpoint must return 200 — Cloud Run depends on this."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_returns_healthy_status():
    """Health endpoint must return healthy status."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_check_returns_environment():
    """Health endpoint must return environment field."""
    response = client.get("/health")
    data = response.json()
    assert "environment" in data


def test_health_check_returns_timestamp():
    """Health endpoint must return timestamp field."""
    response = client.get("/health")
    data = response.json()
    assert "timestamp" in data


# ── Root Endpoint Tests ───────────────────────────────────────

def test_root_returns_200():
    """Root endpoint must return 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_root_returns_service_name():
    """Root endpoint must identify the service."""
    response = client.get("/")
    data = response.json()
    assert data["service"] == "MedFlow Referral Agent"


def test_root_returns_running_status():
    """Root endpoint must confirm service is running."""
    response = client.get("/")
    data = response.json()
    assert data["status"] == "running"


# ── Pub/Sub Webhook Tests ─────────────────────────────────────

def test_pubsub_webhook_accepts_valid_event():
    """
    Webhook must accept valid Pub/Sub storage event.
    Must return 200 and accepted status immediately.
    """
    # Encode a valid Cloud Storage event
    event_data = {"bucket": "medflow-referral-docs-dev", "name": "test-referral.pdf"}
    encoded_data = base64.b64encode(
        json.dumps(event_data).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": {"data": encoded_data},
        "subscription": "projects/medflow-referral-agent/subscriptions/test-sub"
    }

    with patch("src.api.main._process_document_background", new_callable=AsyncMock):
        response = client.post("/webhook/pubsub", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"


def test_pubsub_webhook_returns_document_id():
    """Webhook must return a document_id for tracking."""
    event_data = {"bucket": "test-bucket", "name": "referral.pdf"}
    encoded_data = base64.b64encode(
        json.dumps(event_data).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": {"data": encoded_data},
        "subscription": "test-sub"
    }

    with patch("src.api.main._process_document_background", new_callable=AsyncMock):
        response = client.post("/webhook/pubsub", json=payload)

    data = response.json()
    assert "document_id" in data
    assert data["document_id"].startswith("REF-")


def test_pubsub_webhook_ignores_missing_file_details():
    """
    Webhook must gracefully handle events without file details.
    Returns ignored status — does not crash.
    """
    payload = {
        "message": {"data": ""},
        "subscription": "test-sub"
    }

    response = client.post("/webhook/pubsub", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"


# ── Coordinator Action Tests ──────────────────────────────────

def test_coordinator_approved_action():
    """Coordinator approval must be recorded successfully."""
    payload = {
        "document_id": "REF-12345678",
        "session_id": "test-session-id",
        "action": "approved",
        "coordinator_id": "dr.schmidt@lmu-klinikum.de"
    }

    response = client.post("/coordinator/action", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["action"] == "approved"


def test_coordinator_edited_action():
    """Coordinator edit with department change must be recorded."""
    payload = {
        "document_id": "REF-12345678",
        "session_id": "test-session-id",
        "action": "edited",
        "edited_department": "Cardiology",
        "edited_urgency": "Emergency",
        "coordinator_id": "dr.schmidt@lmu-klinikum.de"
    }

    response = client.post("/coordinator/action", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["action"] == "edited"


def test_coordinator_rejected_action():
    """Coordinator rejection must be recorded successfully."""
    payload = {
        "document_id": "REF-12345678",
        "session_id": "test-session-id",
        "action": "rejected",
        "coordinator_id": "dr.schmidt@lmu-klinikum.de"
    }

    response = client.post("/coordinator/action", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"


def test_coordinator_action_returns_document_id():
    """Coordinator action response must echo back document_id."""
    payload = {
        "document_id": "REF-ABCD1234",
        "session_id": "test-session-id",
        "action": "approved",
        "coordinator_id": "dr.mueller@lmu-klinikum.de"
    }

    response = client.post("/coordinator/action", json=payload)
    data = response.json()
    assert data["document_id"] == "REF-ABCD1234"


def test_coordinator_action_returns_timestamp():
    """Coordinator action response must include timestamp."""
    payload = {
        "document_id": "REF-12345678",
        "session_id": "test-session-id",
        "action": "approved",
        "coordinator_id": "dr.schmidt@lmu-klinikum.de"
    }

    response = client.post("/coordinator/action", json=payload)
    data = response.json()
    assert "timestamp" in data


# ── Referral Status Tests ─────────────────────────────────────

def test_get_referral_status_returns_200():
    """Referral status endpoint must return 200."""
    response = client.get("/referral/REF-12345678")
    assert response.status_code == 200


def test_get_referral_status_returns_document_id():
    """Referral status must echo back the document_id."""
    response = client.get("/referral/REF-12345678")
    data = response.json()
    assert data["document_id"] == "REF-12345678"
