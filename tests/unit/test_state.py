# ============================================================
# Unit Tests — Agent State
# Tests state initialisation
# Tests all required fields are present
# Tests all optional fields start as None
# ============================================================

import pytest
from src.agent.state import ReferralState, create_initial_state


def test_create_initial_state_required_fields():
    """
    Initial state has all required fields set correctly.
    """
    state = create_initial_state(
        document_id="TEST-001",
        document_location="gs://bucket/test.pdf",
        session_id="session-123",
        processing_start_time="2026-05-11T10:00:00+00:00"
    )

    assert state["document_id"] == "TEST-001"
    assert state["document_location"] == "gs://bucket/test.pdf"
    assert state["session_id"] == "session-123"
    assert state["processing_start_time"] == "2026-05-11T10:00:00+00:00"


def test_create_initial_state_optional_fields_are_none():
    """
    All optional fields start as None.
    Nodes fill them in as they execute.
    """
    state = create_initial_state(
        document_id="TEST-001",
        document_location="gs://bucket/test.pdf",
        session_id="session-123",
        processing_start_time="2026-05-11T10:00:00+00:00"
    )

    # Extraction fields
    assert state["document_text"] is None
    assert state["language_detected"] is None
    assert state["extraction_method"] is None
    assert state["extraction_confidence"] is None

    # Routing fields
    assert state["department"] is None
    assert state["routing_confidence"] is None
    assert state["routing_reason"] is None
    assert state["routing_requires_review"] is None

    # Urgency fields
    assert state["urgency"] is None
    assert state["urgency_confidence"] is None
    assert state["urgency_reason"] is None

    # Escalation fields
    assert state["escalation_triggered"] is None
    assert state["escalation_notified_at"] is None

    # Summary field
    assert state["summary"] is None

    # Error fields
    assert state["error"] is None
    assert state["error_node"] is None

    # Coordinator fields
    assert state["coordinator_action"] is None


def test_state_can_be_updated():
    """
    State can be updated by spreading and adding fields.
    This is the pattern used by all nodes.
    """
    state = create_initial_state(
        document_id="TEST-001",
        document_location="gs://bucket/test.pdf",
        session_id="session-123",
        processing_start_time="2026-05-11T10:00:00+00:00"
    )

    # Simulate what extraction node does
    updated_state = {
        **state,
        "document_text": "Patient presenting with chest pain",
        "language_detected": "en",
        "extraction_method": "text",
        "extraction_confidence": 1.0
    }

    # Original state unchanged
    assert state["document_text"] is None

    # Updated state has new values
    assert updated_state["document_text"] == "Patient presenting with chest pain"
    assert updated_state["language_detected"] == "en"

    # Other fields preserved
    assert updated_state["document_id"] == "TEST-001"
    assert updated_state["department"] is None


def test_state_error_fields():
    """
    Error fields can be set correctly.
    Used by nodes for graceful error handling.
    """
    state = create_initial_state(
        document_id="TEST-001",
        document_location="gs://bucket/test.pdf",
        session_id="session-123",
        processing_start_time="2026-05-11T10:00:00+00:00"
    )

    error_state = {
        **state,
        "error": "PDF extraction failed",
        "error_node": "extraction"
    }

    assert error_state["error"] == "PDF extraction failed"
    assert error_state["error_node"] == "extraction"
    assert error_state["document_id"] == "TEST-001"