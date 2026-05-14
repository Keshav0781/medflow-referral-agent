# ============================================================
# Node 2 — Department Routing
# Determines which hospital department receives the referral
# Uses RAG — retrieves department descriptions from ChromaDB
# Calls Gemini 1.5 Pro for reasoning
# Returns department, confidence score, and written reasoning
# ============================================================

import json
import logging
from google import genai
from google.genai import types
from src.agent.state import ReferralState
from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def routing_node(state: ReferralState) -> ReferralState:
    """
    Node 2 — Department Routing

    Receives state with document_text filled in.
    Retrieves relevant department context from ChromaDB.
    Calls Gemini 1.5 Pro to decide routing.
    Returns updated state with department decision.
    """

    logger.info(f"Routing node started for document: {state['document_id']}")

    # ── Check if previous node failed ────────────────────────
    if state.get("error"):
        logger.warning(
            f"Skipping routing — previous error: {state['error']}"
        )
        return state

    # ── Check if document text exists ────────────────────────
    if not state.get("document_text"):
        return {
            **state,
            "error": "No document text available for routing",
            "error_node": "routing",
        }

    try:
        # ── Step 1 — Retrieve department context from ChromaDB
        department_context = _retrieve_department_context(
            state["document_text"]
        )
        logger.info(f"Retrieved {len(department_context)} department contexts")

        # ── Step 2 — Call Gemini 1.5 Pro for routing decision
        routing_result = _call_llm_for_routing(
            document_text=state["document_text"],
            department_context=department_context,
            language=state.get("language_detected", "unknown")
        )

        # ── Step 3 — Check confidence threshold ──────────────
        requires_review = (
            routing_result["confidence"] < settings.routing_confidence_threshold
        )

        if requires_review:
            logger.warning(
                f"Low routing confidence: {routing_result['confidence']} "
                f"below threshold {settings.routing_confidence_threshold}"
            )

        logger.info(
            f"Routing decision: {routing_result['department']} "
            f"confidence: {routing_result['confidence']}"
        )

        # ── Step 4 — Update state with routing decision ───────
        return {
            **state,
            "department": routing_result["department"],
            "routing_confidence": routing_result["confidence"],
            "routing_reason": routing_result["reason"],
            "routing_requires_review": requires_review,
            "error": None,
            "error_node": None,
        }

    except Exception as e:
        error_message = f"Routing failed: {str(e)}"
        logger.error(error_message)

        return {
            **state,
            "department": None,
            "routing_confidence": None,
            "routing_reason": None,
            "routing_requires_review": None,
            "error": error_message,
            "error_node": "routing",
        }


def _retrieve_department_context(document_text: str) -> list[dict]:
    """
    Retrieves relevant department descriptions from ChromaDB.
    Uses semantic search to find most relevant departments.
    Returns top 3 most relevant department descriptions.
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )

        # Use sentence transformers for embedding
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Get departments collection
        collection = client.get_collection(
            name="departments",
            embedding_function=embedding_function
        )

        # Search for relevant departments
        results = collection.query(
            query_texts=[document_text[:1000]],  # Use first 1000 chars
            n_results=3
        )

        # Format results
        contexts = []
        if results["documents"]:
            for doc, metadata in zip(
                results["documents"][0],
                results["metadatas"][0]
            ):
                contexts.append({
                    "department": metadata.get("department_name", "Unknown"),
                    "description": doc
                })

        return contexts

    except Exception as e:
        logger.warning(f"ChromaDB retrieval failed: {e}. Using empty context.")
        return []


def _call_llm_for_routing(
    document_text: str,
    department_context: list[dict],
    language: str
) -> dict:
    """
    Calls Gemini 1.5 Pro to determine department routing.
    Returns department name, confidence score, and reasoning.
    Temperature 0.1 — consistent decisions for clinical routing.
    """

    # Initialise Google GenAI client
    client = genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.vertex_ai_location
    )

    # Format department context for prompt
    context_text = ""
    if department_context:
        context_text = "\n".join([
            f"- {ctx['department']}: {ctx['description']}"
            for ctx in department_context
        ])
    else:
        context_text = "No specific department context available."

    # Build prompt
    prompt = f"""You are a clinical routing assistant at a German hospital.
Your task is to determine which hospital department should receive a patient referral.

RELEVANT DEPARTMENT DESCRIPTIONS:
{context_text}

REFERRAL DOCUMENT ({language.upper()}):
{document_text[:3000]}

TASK:
Analyze the referral and determine the most appropriate department.
Consider the patient's symptoms, diagnosis, and required specialist care.

Respond ONLY with a valid JSON object in this exact format:
{{
    "department": "exact department name",
    "confidence": 0.95,
    "reason": "clear explanation of why this department was chosen"
}}

Rules:
- confidence must be between 0.0 and 1.0
- reason must be in English regardless of document language
- reason must be 1-2 sentences maximum
- department must be one of the available departments"""

    # Call Gemini with low temperature for consistency
    response = client.models.generate_content(
        model=settings.vertex_ai_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=3000,
        )
    )

    # Parse JSON response
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
    required_fields = ["department", "confidence", "reason"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Missing field in LLM response: {field}")

    # Validate confidence range
    if not 0.0 <= result["confidence"] <= 1.0:
        raise ValueError(f"Invalid confidence value: {result['confidence']}")

    return result