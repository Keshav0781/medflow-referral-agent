# ============================================================
# Node 3 — Urgency Classification
# Classifies referral as Routine, Semi-urgent, or Emergency
# Most critical node — patient safety implications
# Uses RAG for clinical urgency guidelines
# Calls Gemini 1.5 Pro with temperature 0.1
# ============================================================

import json
import logging
from google import genai
from google.genai import types
from src.agent.state import ReferralState
from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Valid urgency levels — only these three accepted
VALID_URGENCY_LEVELS = {"Routine", "Semi-urgent", "Emergency"}


def urgency_node(state: ReferralState) -> ReferralState:
    """
    Node 3 — Urgency Classification

    Receives state with document_text and department filled in.
    Retrieves urgency guidelines from ChromaDB.
    Calls Gemini 1.5 Pro to classify urgency.
    Returns updated state with urgency classification.

    Only three valid outputs: Routine, Semi-urgent, Emergency
    When uncertain — always classify higher urgency.
    Patient safety is paramount.
    """

    logger.info(f"Urgency node started for document: {state['document_id']}")

    # ── Check if previous node failed ────────────────────────
    if state.get("error"):
        logger.warning(
            f"Skipping urgency — previous error: {state['error']}"
        )
        return state

    # ── Check required fields exist ───────────────────────────
    if not state.get("document_text"):
        return {
            **state,
            "error": "No document text available for urgency classification",
            "error_node": "urgency",
        }

    try:
        # ── Step 1 — Retrieve urgency guidelines from ChromaDB
        urgency_guidelines = _retrieve_urgency_guidelines(
            state["document_text"]
        )
        logger.info(f"Retrieved {len(urgency_guidelines)} urgency guidelines")

        # ── Step 2 — Call Gemini 1.5 Pro ─────────────────────
        urgency_result = _call_llm_for_urgency(
            document_text=state["document_text"],
            department=state.get("department", "Unknown"),
            urgency_guidelines=urgency_guidelines,
            language=state.get("language_detected", "unknown")
        )

        # ── Step 3 — Validate urgency level ──────────────────
        if urgency_result["urgency"] not in VALID_URGENCY_LEVELS:
            logger.warning(
                f"Invalid urgency level returned: {urgency_result['urgency']}. "
                f"Defaulting to Semi-urgent for patient safety."
            )
            urgency_result["urgency"] = "Semi-urgent"
            urgency_result["confidence"] = 0.5
            urgency_result["reason"] = (
                f"Original classification '{urgency_result['urgency']}' "
                f"was invalid. Defaulted to Semi-urgent for patient safety."
            )

        logger.info(
            f"Urgency classification: {urgency_result['urgency']} "
            f"confidence: {urgency_result['confidence']}"
        )

        # ── Step 4 — Update state ─────────────────────────────
        return {
            **state,
            "urgency": urgency_result["urgency"],
            "urgency_confidence": urgency_result["confidence"],
            "urgency_reason": urgency_result["reason"],
            "error": None,
            "error_node": None,
        }

    except Exception as e:
        error_message = f"Urgency classification failed: {str(e)}"
        logger.error(error_message)

        # ── Safety fallback on error ──────────────────────────
        # If urgency classification fails completely —
        # default to Semi-urgent rather than Routine.
        # Better to over-triage than under-triage.
        logger.warning(
            "Urgency classification failed — defaulting to Semi-urgent "
            "for patient safety"
        )

        return {
            **state,
            "urgency": "Semi-urgent",
            "urgency_confidence": 0.0,
            "urgency_reason": (
                "Urgency classification failed due to system error. "
                "Defaulted to Semi-urgent for patient safety. "
                "Please review manually."
            ),
            "error": error_message,
            "error_node": "urgency",
        }


def _retrieve_urgency_guidelines(document_text: str) -> list[dict]:
    """
    Retrieves relevant urgency guidelines from ChromaDB.
    Uses semantic search to find most relevant guidelines.
    Returns top 3 most relevant urgency indicators.
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )

        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        collection = client.get_collection(
            name="urgency_guidelines",
            embedding_function=embedding_function
        )

        results = collection.query(
            query_texts=[document_text[:1000]],
            n_results=3
        )

        guidelines = []
        if results["documents"]:
            for doc, metadata in zip(
                results["documents"][0],
                results["metadatas"][0]
            ):
                guidelines.append({
                    "level": metadata.get("urgency_level", "Unknown"),
                    "description": doc
                })

        return guidelines

    except Exception as e:
        logger.warning(
            f"ChromaDB urgency retrieval failed: {e}. "
            f"Using empty guidelines."
        )
        return []


def _call_llm_for_urgency(
    document_text: str,
    department: str,
    urgency_guidelines: list[dict],
    language: str
) -> dict:
    """
    Calls Gemini 1.5 Pro to classify urgency.
    Temperature 0.1 — consistent decisions for patient safety.

    Critical instruction: when uncertain — classify higher urgency.
    Better to over-triage than under-triage.
    """

    client = genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.vertex_ai_location
    )

    # Format urgency guidelines
    guidelines_text = ""
    if urgency_guidelines:
        guidelines_text = "\n".join([
            f"- {g['level']}: {g['description']}"
            for g in urgency_guidelines
        ])
    else:
        guidelines_text = """
- Emergency: Immediate life-threatening conditions requiring 
  same-day or immediate specialist attention. Examples: 
  stroke symptoms, severe chest pain, acute respiratory 
  distress, signs of sepsis, sudden vision loss.
- Semi-urgent: Significant conditions requiring specialist 
  attention within 48 hours. Examples: concerning ECG changes,
  progressive neurological symptoms, suspected malignancy 
  with rapid progression.
- Routine: Stable conditions for scheduled specialist 
  appointment within 1-2 weeks. Examples: chronic condition 
  management, routine follow-up, stable symptoms.
"""

    prompt = f"""You are a clinical urgency classifier at a German hospital.
Your task is to classify the urgency of a patient referral.

URGENCY GUIDELINES:
{guidelines_text}

ROUTING DECISION:
Department: {department}

REFERRAL DOCUMENT ({language.upper()}):
{document_text[:3000]}

TASK:
Classify the urgency of this referral.
You must choose exactly one of: Routine, Semi-urgent, Emergency

IMPORTANT RULES:
1. When uncertain — always classify HIGHER urgency
2. Patient safety is more important than efficiency
3. Emergency means same-day or immediate action needed
4. Semi-urgent means within 48 hours
5. Routine means within 1-2 weeks is acceptable

Respond ONLY with a valid JSON object in this exact format:
{{
    "urgency": "Semi-urgent",
    "confidence": 0.89,
    "reason": "clear clinical reasoning for this urgency level"
}}

Rules:
- urgency must be exactly one of: Routine, Semi-urgent, Emergency
- confidence must be between 0.0 and 1.0
- reason must be in English
- reason must be 1-2 sentences maximum
- if uncertain between two levels — choose the higher urgency"""

    response = client.models.generate_content(
        model=settings.vertex_ai_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=1000,
        )
    )

    response_text = response.text.strip()

    # Extract JSON object robustly — handles markdown blocks and
    # chain-of-thought reasoning text before/after the JSON
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]
    else:
        # Extract first complete JSON object from response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            response_text = response_text[start:end]

    result = json.loads(response_text.strip())

    # Validate required fields
    required_fields = ["urgency", "confidence", "reason"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Missing field in LLM response: {field}")

    # Validate confidence range
    if not 0.0 <= result["confidence"] <= 1.0:
        raise ValueError(f"Invalid confidence: {result['confidence']}")

    return result