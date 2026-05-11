# ============================================================
# MedFlow Referral Agent - State Definition
# Defines the shared state that flows through all agent nodes
# Think of it as the whiteboard every node reads and writes to
# One state instance per document being processed
# ============================================================

from typing import Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ReferralState(TypedDict):
    """
    Complete state for one referral document processing run.
    Every node reads from and writes to this shared state.
    Fields start as None and get filled as nodes execute.
    """

    # ── Document Information ─────────────────────────────────
    # Set at the start — never changes during processing
    document_id: str
    document_location: str
    session_id: str

    # ── Extraction Node Output ───────────────────────────────
    # Filled by Node 1 — extraction node
    document_text: Optional[str]
    language_detected: Optional[str]
    extraction_method: Optional[str]  # text or ocr
    extraction_confidence: Optional[float]

    # ── Routing Node Output ──────────────────────────────────
    # Filled by Node 2 — routing node
    department: Optional[str]
    routing_confidence: Optional[float]
    routing_reason: Optional[str]
    routing_requires_review: Optional[bool]  # True if confidence below threshold

    # ── Urgency Node Output ──────────────────────────────────
    # Filled by Node 3 — urgency classification node
    urgency: Optional[str]  # Routine, Semi-urgent, Emergency
    urgency_confidence: Optional[float]
    urgency_reason: Optional[str]

    # ── Escalation Node Output ───────────────────────────────
    # Filled by Node 4 — escalation check node
    escalation_triggered: Optional[bool]
    escalation_notified_at: Optional[str]

    # ── Summary Node Output ──────────────────────────────────
    # Filled by Node 5 — summary generation node
    summary: Optional[str]

    # ── Processing Metadata ──────────────────────────────────
    processing_start_time: Optional[str]
    processing_end_time: Optional[str]
    processing_time_seconds: Optional[float]

    # ── LangSmith Tracing ────────────────────────────────────
    langsmith_trace_id: Optional[str]

    # ── Error Handling ───────────────────────────────────────
    # If any node fails — error details stored here
    # Other nodes check this and handle gracefully
    error: Optional[str]
    error_node: Optional[str]  # which node failed

    # ── Coordinator Review ───────────────────────────────────
    # Filled after coordinator reviews and acts
    coordinator_action: Optional[str]  # approved, edited, rejected
    coordinator_edited_department: Optional[str]
    coordinator_edited_urgency: Optional[str]


def create_initial_state(
    document_id: str,
    document_location: str,
    session_id: str,
    processing_start_time: str
) -> ReferralState:
    """
    Creates the initial state for a new document processing run.
    All optional fields start as None.
    Called at the start of every agent run.
    """
    return ReferralState(
        # Document information — always provided
        document_id=document_id,
        document_location=document_location,
        session_id=session_id,

        # Extraction — empty until Node 1 runs
        document_text=None,
        language_detected=None,
        extraction_method=None,
        extraction_confidence=None,

        # Routing — empty until Node 2 runs
        department=None,
        routing_confidence=None,
        routing_reason=None,
        routing_requires_review=None,

        # Urgency — empty until Node 3 runs
        urgency=None,
        urgency_confidence=None,
        urgency_reason=None,

        # Escalation — empty until Node 4 runs
        escalation_triggered=None,
        escalation_notified_at=None,

        # Summary — empty until Node 5 runs
        summary=None,

        # Processing metadata
        processing_start_time=processing_start_time,
        processing_end_time=None,
        processing_time_seconds=None,

        # LangSmith
        langsmith_trace_id=None,

        # Errors — empty unless something goes wrong
        error=None,
        error_node=None,

        # Coordinator — empty until coordinator acts
        coordinator_action=None,
        coordinator_edited_department=None,
        coordinator_edited_urgency=None,
    )