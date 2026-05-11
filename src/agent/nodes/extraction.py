# ============================================================
# Node 1 — Document Extraction
# Reads PDF from Cloud Storage
# Extracts text using PyMuPDF
# Falls back to OCR for scanned images
# Detects document language
# Does NOT call LLM — uses specialised tools only
# ============================================================

import fitz  # PyMuPDF
import uuid
import logging
from datetime import datetime, timezone
from google.cloud import storage
from src.agent.state import ReferralState
from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def extraction_node(state: ReferralState) -> ReferralState:
    """
    Node 1 — Document Extraction

    Receives state with document_location filled in.
    Extracts text from PDF document.
    Returns updated state with document_text filled in.

    No LLM call — uses PyMuPDF and Cloud Vision only.
    """

    logger.info(f"Extraction node started for document: {state['document_id']}")

    try:
        # ── Step 1 — Download PDF from Cloud Storage ─────────
        pdf_bytes = _download_from_cloud_storage(state['document_location'])
        logger.info(f"Downloaded PDF — size: {len(pdf_bytes)} bytes")

        # ── Step 2 — Try text extraction with PyMuPDF ────────
        extracted_text, method, confidence = _extract_text(pdf_bytes)

        # ── Step 3 — Detect language ──────────────────────────
        language = _detect_language(extracted_text)
        logger.info(f"Language detected: {language}")

        # ── Step 4 — Validate extracted text ─────────────────
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise ValueError(
                f"Extracted text too short: {len(extracted_text)} characters. "
                f"Document may be corrupted or empty."
            )

        logger.info(
            f"Extraction complete — method: {method}, "
            f"confidence: {confidence}, "
            f"text length: {len(extracted_text)}"
        )

        # ── Step 5 — Update state with results ───────────────
        return {
            **state,
            "document_text": extracted_text.strip(),
            "language_detected": language,
            "extraction_method": method,
            "extraction_confidence": confidence,
            "error": None,
            "error_node": None,
        }

    except Exception as e:
        # ── Error handling — graceful degradation ─────────────
        error_message = f"Extraction failed: {str(e)}"
        logger.error(error_message)

        return {
            **state,
            "document_text": None,
            "language_detected": None,
            "extraction_method": None,
            "extraction_confidence": None,
            "error": error_message,
            "error_node": "extraction",
        }


def _download_from_cloud_storage(document_location: str) -> bytes:
    """
    Downloads PDF bytes from Cloud Storage.
    document_location format: gs://bucket-name/file-path
    """
    # Parse bucket and blob from gs:// URL
    # gs://medflow-referral-docs-dev-medflow-referral-agent/REF-001.pdf
    path = document_location.replace("gs://", "")
    bucket_name, blob_name = path.split("/", 1)

    storage_client = storage.Client(project=settings.gcp_project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    return blob.download_as_bytes()


def _extract_text(pdf_bytes: bytes) -> tuple[str, str, float]:
    """
    Extracts text from PDF bytes.
    First tries PyMuPDF for text-based PDFs.
    Falls back to OCR for scanned image PDFs.

    Returns:
        text: extracted text content
        method: 'text' or 'ocr'
        confidence: extraction confidence score
    """
    # Try PyMuPDF first — fast and free
    text = _extract_with_pymupdf(pdf_bytes)

    if text and len(text.strip()) > 50:
        # Enough text extracted — PDF is text-based
        return text, "text", 1.0

    # Not enough text — PDF is likely a scanned image
    # Fall back to Google Cloud Vision OCR
    logger.info("PyMuPDF extracted insufficient text — falling back to OCR")
    text, confidence = _extract_with_ocr(pdf_bytes)
    return text, "ocr", confidence


def _extract_with_pymupdf(pdf_bytes: bytes) -> str:
    """
    Extracts text from PDF using PyMuPDF.
    Works for text-based PDFs.
    Returns empty string for scanned image PDFs.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page in doc:
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(page_text)

        doc.close()
        return "\n".join(text_parts)

    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}")
        return ""


def _extract_with_ocr(pdf_bytes: bytes) -> tuple[str, float]:
    """
    Extracts text from scanned PDF using Google Cloud Vision OCR.
    More expensive than PyMuPDF but handles scanned documents.

    Returns:
        text: extracted text
        confidence: OCR confidence score 0.0 to 1.0
    """
    try:
        from google.cloud import vision

        vision_client = vision.ImageAnnotatorClient()

        # Convert PDF bytes to image for OCR
        image = vision.Image(content=pdf_bytes)
        response = vision_client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")

        full_text = response.full_text_annotation.text

        # Calculate average confidence from all detected text blocks
        confidences = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                confidences.append(block.confidence)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        logger.info(f"OCR completed — confidence: {avg_confidence:.2f}")
        return full_text, avg_confidence

    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return "", 0.0


def _detect_language(text: str) -> str:
    """
    Detects language of extracted text.
    Uses simple heuristic — checks for German specific characters.
    Returns language code: 'de', 'en', 'tr', or 'unknown'

    In production — replace with proper language detection library.
    """
    if not text:
        return "unknown"

    # German specific characters
    german_chars = set("äöüÄÖÜß")
    text_chars = set(text)

    # Count German specific characters
    german_count = len(german_chars.intersection(text_chars))

    if german_count >= 2:
        return "de"

    # Simple English heuristic — common English words
    english_words = {"the", "and", "patient", "dear", "please", "referred"}
    text_lower = text.lower()
    english_count = sum(1 for word in english_words if word in text_lower)

    if english_count >= 2:
        return "en"

    # Turkish common characters
    turkish_chars = set("şğıİŞĞ")
    turkish_count = len(turkish_chars.intersection(text_chars))

    if turkish_count >= 1:
        return "tr"

    return "unknown"