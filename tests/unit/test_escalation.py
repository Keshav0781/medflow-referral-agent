# ============================================================
# Unit Tests — Escalation Node
# Tests Emergency detection logic
# Tests non-Emergency cases
# Tests error state handling
# No LLM calls — pure logic testing
# ============================================================

import pytest
from src.agent.state import create_initial_state
from src.agent.nodes.escalation import escalation_node


def _make_state(urgency: str, error: str = None) -> dict:
    """Helper — creates state with urgency set."""
    state = create_initial_state(
        document_id="TEST-001",
        document_location="gs://bucket/test.pdf",
        session_id="session-123",
        processing_start_time="2026-05-11T10:00:00+00:00"
    )
    return {
        **state,
        "document_text": "Patient referral text",
        "department": "Cardiology",
        "urgency": urgency,
        "urgency_reason": "Test reason",
        "error": error,
        "error_node": "urgency" if error else None
    }


def test_emergency_triggers_escalation():
    """
    Emergency urgency triggers escalation.
    escalation_triggered must be True.
    escalation_notified_at must be set.
    """
    state = _make_state("Emergency")
    result = escalation_node(state)

    assert result["escalation_triggered"] is True
    assert result["escalation_notified_at"] is not None


def test_semi_urgent_no_escalation():
    """
    Semi-urgent urgency does not trigger escalation.
    escalation_triggered must be False.
    """
    state = _make_state("Semi-urgent")
    result = escalation_node(state)

    assert result["escalation_triggered"] is False
    assert result["escalation_notified_at"] is None


def test_routine_no_escalation():
    """
    Routine urgency does not trigger escalation.
    escalation_triggered must be False.
    """
    state = _make_state("Routine")
    result = escalation_node(state)

    assert result["escalation_triggered"] is False
    assert result["escalation_notified_at"] is None


def test_escalation_preserves_state():
    """
    Escalation node preserves all existing state fields.
    Only adds escalation fields.
    """
    state = _make_state("Emergency")
    result = escalation_node(state)

    assert result["document_id"] == "TEST-001"
    assert result["department"] == "Cardiology"
    assert result["urgency"] == "Emergency"


def test_escalation_runs_with_previous_error():
    """
    Escalation node runs even when previous node had error.
    This is intentional — urgency defaults to Semi-urgent on error.
    Semi-urgent does not trigger escalation.
    """
    state = _make_state(
        urgency="Semi-urgent",
        error="Urgency classification failed"
    )
    result = escalation_node(state)

    assert result["escalation_triggered"] is False
    assert result["error"] == "Urgency classification failed"


def test_escalation_timestamp_format():
    """
    Escalation timestamp is in ISO format.
    Required for BigQuery audit logging.
    """
    state = _make_state("Emergency")
    result = escalation_node(state)

    assert result["escalation_triggered"] is True
    timestamp = result["escalation_notified_at"]

    # Verify it is a valid ISO timestamp string
    assert isinstance(timestamp, str)
    assert "T" in timestamp
    assert len(timestamp) > 10