# ============================================================
# Node 4 — Escalation Check
# Checks if urgency is Emergency
# If Emergency — immediately notifies on-call staff
# Does NOT wait for coordinator approval for Emergency
# Does NOT call LLM — simple conditional check only
# ============================================================

import logging
from datetime import datetime, timezone
from src.agent.state import ReferralState
from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def escalation_node(state: ReferralState) -> ReferralState:
    """
    Node 4 — Escalation Check

    Receives state with urgency filled in.
    If urgency is Emergency — sends immediate notification.
    Does not wait for coordinator approval.
    Returns updated state with escalation details.

    No LLM call — simple conditional logic only.
    """

    logger.info(f"Escalation node started for document: {state['document_id']}")

    # ── Check if previous node failed ────────────────────────
    # Note: we still run escalation even if there was an error
    # because urgency defaults to Semi-urgent on error
    # Semi-urgent does not trigger escalation
    # So safe to continue even with errors

    urgency = state.get("urgency", "Semi-urgent")

    # ── Check if Emergency ────────────────────────────────────
    if urgency == "Emergency":
        logger.warning(
            f"EMERGENCY case detected — document: {state['document_id']} "
            f"department: {state.get('department', 'Unknown')}"
        )

        # Send immediate notification
        notification_sent = _send_emergency_notification(state)

        escalation_time = datetime.now(timezone.utc).isoformat()

        logger.warning(
            f"Emergency escalation triggered at {escalation_time} "
            f"notification sent: {notification_sent}"
        )

        return {
            **state,
            "escalation_triggered": True,
            "escalation_notified_at": escalation_time,
        }

    else:
        # Not Emergency — no escalation needed
        logger.info(
            f"No escalation needed — urgency: {urgency}"
        )

        return {
            **state,
            "escalation_triggered": False,
            "escalation_notified_at": None,
        }


def _send_emergency_notification(state: ReferralState) -> bool:
    """
    Sends immediate notification for Emergency cases.
    Notifies on-call department head and coordinator simultaneously.

    In production — integrates with hospital notification system.
    Currently logs the notification for audit purposes.

    Returns True if notification was sent successfully.
    """

    try:
        department = state.get("department", "Unknown Department")
        document_id = state.get("document_id", "Unknown")
        urgency_reason = state.get("urgency_reason", "No reason provided")

        # ── Notification Message ──────────────────────────────
        notification_message = f"""
EMERGENCY REFERRAL ALERT
========================
Document ID: {document_id}
Department: {department}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Clinical Reason:
{urgency_reason}

ACTION REQUIRED:
This referral has been classified as EMERGENCY.
Immediate attention required.
Please review the full referral in the MedFlow platform.
========================
        """.strip()

        # Log the notification — audit trail
        logger.warning(f"EMERGENCY NOTIFICATION:\n{notification_message}")

        # In production — send via hospital notification API
        # Example integrations:
        # - Email to on-call department head
        # - SMS via Twilio
        # - Push notification via platform
        # - Integration with hospital paging system
        # Currently logging only — integration added in Phase 2

        return True

    except Exception as e:
        logger.error(f"Failed to send emergency notification: {e}")
        return False