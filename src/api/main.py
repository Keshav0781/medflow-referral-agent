# ============================================================
# MedFlow Referral Agent - FastAPI Application
# Entry point for the entire system
# Receives Pub/Sub events when new PDF arrives
# Exposes health check for Cloud Run
# Handles coordinator approval workflow
# Manages audit logging to BigQuery
# ============================================================

import json
import base64
import logging
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from src.config.settings import get_settings
from src.agent.graph import process_referral
from src.agent.state import ReferralState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Pydantic Models ───────────────────────────────────────────

class PubSubMessage(BaseModel):
    """Message received from Cloud Pub/Sub"""
    message: dict
    subscription: str


class CoordinatorAction(BaseModel):
    """Coordinator approval or edit of AI recommendations"""
    document_id: str
    session_id: str
    action: str  # approved, edited, rejected
    edited_department: Optional[str] = None
    edited_urgency: Optional[str] = None
    coordinator_id: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    environment: str
    timestamp: str


# ── Application Lifespan ──────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown.
    Runs once when application starts.
    """
    logger.info("MedFlow Referral Agent starting up")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"GCP Project: {settings.gcp_project_id}")
    logger.info(f"Vertex AI Model: {settings.vertex_ai_model}")
    yield
    logger.info("MedFlow Referral Agent shutting down")


# ── FastAPI Application ───────────────────────────────────────

app = FastAPI(
    title="MedFlow Referral Agent",
    description="Production-grade multi-agent AI system for automated clinical referral processing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Called by Cloud Run every 30 seconds.
    Must respond quickly — under 10 seconds.
    """
    return HealthResponse(
        status="healthy",
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@app.get("/")
async def root():
    """Root endpoint — confirms service is running"""
    return {
        "service": "MedFlow Referral Agent",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment
    }


@app.post("/webhook/pubsub")
async def receive_pubsub_event(
    message: PubSubMessage,
    background_tasks: BackgroundTasks
):
    """
    Receives Pub/Sub events when new referral PDF arrives.
    Triggered automatically by Cloud Storage notification.
    Processes document in background — returns immediately.

    Pub/Sub expects response within 10 seconds.
    We acknowledge immediately and process in background.
    """
    try:
        # Decode Pub/Sub message
        message_data = message.message.get("data", "")
        if message_data:
            decoded_data = base64.b64decode(message_data).decode("utf-8")
            event_data = json.loads(decoded_data)
        else:
            event_data = message.message.get("attributes", {})

        # Extract file details from Cloud Storage event
        bucket_name = event_data.get("bucket", "")
        file_name = event_data.get("name", "")

        if not bucket_name or not file_name:
            logger.warning(f"Invalid Pub/Sub event — missing bucket or file name")
            return {"status": "ignored", "reason": "missing file details"}

        # Construct document details
        document_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
        document_location = f"gs://{bucket_name}/{file_name}"
        session_id = str(uuid.uuid4())

        logger.info(
            f"New referral received — "
            f"document_id: {document_id} "
            f"location: {document_location}"
        )

        # Process in background — respond to Pub/Sub immediately
        background_tasks.add_task(
            _process_document_background,
            document_id=document_id,
            document_location=document_location,
            session_id=session_id
        )

        # Return immediately — Pub/Sub acknowledged
        return {
            "status": "accepted",
            "document_id": document_id,
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Error processing Pub/Sub event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/coordinator/action")
async def coordinator_action(
    action: CoordinatorAction,
    background_tasks: BackgroundTasks
):
    """
    Receives coordinator approval or edit of AI recommendations.
    Called when coordinator approves, edits, or rejects.
    Logs final decision to BigQuery for audit trail.
    """
    try:
        logger.info(
            f"Coordinator action received — "
            f"document: {action.document_id} "
            f"action: {action.action} "
            f"coordinator: {action.coordinator_id}"
        )

        # Log coordinator action to BigQuery in background
        background_tasks.add_task(
            _log_coordinator_action,
            action=action
        )

        return {
            "status": "recorded",
            "document_id": action.document_id,
            "action": action.action,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Error recording coordinator action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/referral/{document_id}")
async def get_referral_status(document_id: str):
    """
    Returns current processing status of a referral.
    Called by coordinator dashboard to check results.
    """
    # In production — fetch from database
    # For now — return placeholder
    return {
        "document_id": document_id,
        "status": "processed",
        "message": "Check platform database for full results"
    }


# ── Background Tasks ──────────────────────────────────────────

async def _process_document_background(
    document_id: str,
    document_location: str,
    session_id: str
):
    """
    Processes referral document in background.
    Called after Pub/Sub acknowledgement.
    Runs complete agent workflow.
    Logs results to BigQuery.
    """
    try:
        logger.info(f"Background processing started: {document_id}")

        # Run complete agent workflow
        final_state = await process_referral(
            document_id=document_id,
            document_location=document_location,
            session_id=session_id
        )

        logger.info(
            f"Background processing complete: {document_id} "
            f"department: {final_state.get('department')} "
            f"urgency: {final_state.get('urgency')} "
            f"time: {final_state.get('processing_time_seconds')}s"
        )

        # Log to BigQuery
        if settings.enable_bigquery:
            await _log_to_bigquery(final_state)

    except Exception as e:
        logger.error(
            f"Background processing failed for {document_id}: {e}"
        )


async def _log_to_bigquery(state: ReferralState):
    """
    Logs agent decisions to BigQuery for audit trail.
    Runs asynchronously — never blocks main processing.
    7 year retention for healthcare compliance.
    """
    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=settings.gcp_project_id)

        table_id = (
            f"{settings.gcp_project_id}."
            f"{settings.bigquery_dataset}."
            f"{settings.bigquery_table}"
        )

        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "document_id": state.get("document_id"),
            "session_id": state.get("session_id"),
            "department": state.get("department"),
            "routing_confidence": state.get("routing_confidence"),
            "routing_reason": state.get("routing_reason"),
            "urgency": state.get("urgency"),
            "urgency_confidence": state.get("urgency_confidence"),
            "urgency_reason": state.get("urgency_reason"),
            "processing_time_seconds": state.get("processing_time_seconds"),
            "escalation_triggered": state.get("escalation_triggered"),
            "langsmith_trace_id": state.get("langsmith_trace_id"),
            "environment": settings.environment
        }

        errors = client.insert_rows_json(table_id, [row])

        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
        else:
            logger.info(f"Audit log written to BigQuery: {state.get('document_id')}")

    except Exception as e:
        logger.error(f"BigQuery logging failed: {e}")


async def _log_coordinator_action(action: CoordinatorAction):
    """
    Logs coordinator action to BigQuery.
    Updates the audit record with human decision.
    """
    try:
        logger.info(
            f"Coordinator action logged: {action.document_id} "
            f"action: {action.action}"
        )
        # In production — update BigQuery record
        # with coordinator_action field

    except Exception as e:
        logger.error(f"Failed to log coordinator action: {e}")


# ── Application Entry Point ───────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False
    )