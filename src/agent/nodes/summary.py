# ============================================================
# Node 5 — Summary Generation
# Generates structured plain-language summary for department
# Uses document text, routing decision, and urgency context
# Calls Gemini 1.5 Pro with temperature 0.3
# Maximum 150 words — concise and actionable
# ============================================================

import logging
from google import genai
from google.genai import types
from src.agent.state import ReferralState
from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def summary_node(state: ReferralState) -> ReferralState:
    """
    Node 5 — Summary Generation

    Receives state with document_text, department,
    urgency, and urgency_reason filled in.
    Generates concise structured summary for department.
    Returns updated state with summary filled in.
    """

    logger.info(f"Summary node started for document: {state['document_id']}")

    # ── Check required fields ─────────────────────────────────
    if not state.get("document_text"):
        return {
            **state,
            "summary": "Summary could not be generated — no document text available.",
            "error": state.get("error"),
            "error_node": state.get("error_node"),
        }

    try:
        # ── Call Gemini 1.5 Pro for summary ───────────────────
        summary = _call_llm_for_summary(
            document_text=state["document_text"],
            department=state.get("department", "Unknown Department"),
            urgency=state.get("urgency", "Semi-urgent"),
            urgency_reason=state.get("urgency_reason", ""),
            language=state.get("language_detected", "unknown")
        )

        logger.info(
            f"Summary generated — length: {len(summary)} characters"
        )

        return {
            **state,
            "summary": summary,
        }

    except Exception as e:
        error_message = f"Summary generation failed: {str(e)}"
        logger.error(error_message)

        # ── Fallback summary on error ─────────────────────────
        # Even if summary generation fails — provide basic info
        # Coordinator can still see department and urgency
        fallback_summary = (
            f"Automated summary could not be generated. "
            f"Department: {state.get('department', 'Unknown')}. "
            f"Urgency: {state.get('urgency', 'Unknown')}. "
            f"Please review the original referral document manually."
        )

        return {
            **state,
            "summary": fallback_summary,
            "error": error_message,
            "error_node": "summary",
        }


def _call_llm_for_summary(
    document_text: str,
    department: str,
    urgency: str,
    urgency_reason: str,
    language: str
) -> str:
    """
    Calls Gemini 1.5 Pro to generate referral summary.
    Temperature 0.3 — slight variation for natural language
    while maintaining factual accuracy.
    Maximum 150 words — concise and actionable.
    """

    client = genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.vertex_ai_location
    )

    prompt = f"""You are a clinical documentation assistant at a German hospital.
Your task is to write a clear concise summary of a patient referral
for the receiving department.

ROUTING DECISION:
Department: {department}
Urgency: {urgency}
Urgency Reason: {urgency_reason}

REFERRAL DOCUMENT ({language.upper()}):
{document_text[:3000]}

TASK:
Write a structured summary for the {department} department.
The summary will be read by specialist doctors and nurses.

REQUIREMENTS:
- Maximum 150 words
- Plain language — avoid unnecessary medical jargon
- Must include: patient age and gender if mentioned
- Must include: main reason for referral
- Must include: key symptoms or findings
- Must include: urgency context and timing
- Must include: referring doctor if mentioned
- Write in English regardless of document language
- Be factual — only include information from the document
- Do not add information not present in the document

Write the summary directly — no introduction or preamble."""

    response = client.models.generate_content(
        model=settings.vertex_ai_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=3000,
        )
    )

    summary = response.text.strip()

    # Validate summary is not empty
    if not summary:
        raise ValueError("Empty summary returned from LLM")

    # Truncate if somehow exceeds limit
    words = summary.split()
    if len(words) > 160:
        summary = " ".join(words[:150]) + "..."
        logger.warning("Summary truncated to 150 words")

    return summary