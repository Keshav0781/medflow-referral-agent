# ============================================================
# RAG Ingestion
# Loads department descriptions and urgency guidelines
# into ChromaDB vector database
# Run once during setup — not during document processing
# Creates two collections:
#   1. departments — for routing node
#   2. urgency_guidelines — for urgency node
# ============================================================

import logging
import chromadb
from chromadb.utils import embedding_functions
logger = logging.getLogger(__name__)
CHROMA_PERSIST_DIR = "./data/chroma"

# ── Department Descriptions ───────────────────────────────────
# What each department treats
# Used by routing node to match referral to department
# In production — loaded from hospital configuration
# These are generic descriptions for LMU Klinikum pilot

DEPARTMENT_DESCRIPTIONS = [
    {
        "id": "dept_cardiology",
        "department_name": "Cardiology",
        "description": (
            "Cardiology department treats conditions related to the heart "
            "and cardiovascular system. Specialises in chest pain, heart "
            "failure, arrhythmia, coronary artery disease, heart valve "
            "problems, hypertension, and cardiac risk assessment. Performs "
            "ECG analysis, echocardiography, and cardiac catheterisation."
        )
    },
    {
        "id": "dept_neurology",
        "department_name": "Neurology",
        "description": (
            "Neurology department treats conditions of the brain, spinal "
            "cord, and nervous system. Specialises in stroke, epilepsy, "
            "multiple sclerosis, Parkinson's disease, dementia, migraine, "
            "neuropathy, and movement disorders. Performs EEG, nerve "
            "conduction studies, and neurological assessments."
        )
    },
    {
        "id": "dept_oncology",
        "department_name": "Oncology",
        "description": (
            "Oncology department diagnoses and treats cancer. Specialises "
            "in solid tumours, haematological malignancies, chemotherapy, "
            "immunotherapy, and cancer staging. Works with suspected "
            "malignancies, abnormal tumour markers, unexplained weight "
            "loss, and cancer follow-up care."
        )
    },
    {
        "id": "dept_orthopedics",
        "department_name": "Orthopedics",
        "description": (
            "Orthopedics department treats conditions of the "
            "musculoskeletal system. Specialises in bone fractures, joint "
            "replacement, spine disorders, sports injuries, arthritis, "
            "and tendon problems. Treats back pain, knee pain, hip pain, "
            "and shoulder conditions."
        )
    },
    {
        "id": "dept_gastroenterology",
        "department_name": "Gastroenterology",
        "description": (
            "Gastroenterology department treats digestive system "
            "conditions. Specialises in stomach disorders, intestinal "
            "conditions, liver disease, inflammatory bowel disease, "
            "colorectal cancer screening, and endoscopy. Treats abdominal "
            "pain, reflux, dysphagia, and bowel disorders."
        )
    },
    {
        "id": "dept_pulmonology",
        "department_name": "Pulmonology",
        "description": (
            "Pulmonology department treats respiratory system conditions. "
            "Specialises in asthma, COPD, pneumonia, lung cancer, sleep "
            "apnea, pulmonary fibrosis, and breathing disorders. Performs "
            "spirometry, bronchoscopy, and pulmonary function tests."
        )
    },
    {
        "id": "dept_endocrinology",
        "department_name": "Endocrinology",
        "description": (
            "Endocrinology department treats hormonal and metabolic "
            "conditions. Specialises in diabetes, thyroid disorders, "
            "adrenal conditions, pituitary disorders, osteoporosis, and "
            "metabolic syndrome. Manages insulin therapy and hormone "
            "replacement treatment."
        )
    },
    {
        "id": "dept_nephrology",
        "department_name": "Nephrology",
        "description": (
            "Nephrology department treats kidney conditions. Specialises "
            "in chronic kidney disease, acute kidney injury, kidney "
            "stones, hypertensive nephropathy, dialysis management, and "
            "kidney transplant follow-up. Monitors renal function and "
            "electrolyte disorders."
        )
    },
    {
        "id": "dept_rheumatology",
        "department_name": "Rheumatology",
        "description": (
            "Rheumatology department treats autoimmune and inflammatory "
            "conditions. Specialises in rheumatoid arthritis, lupus, "
            "gout, vasculitis, and connective tissue disorders. Manages "
            "joint inflammation, autoimmune conditions, and "
            "immunosuppressive therapy."
        )
    },
    {
        "id": "dept_dermatology",
        "department_name": "Dermatology",
        "description": (
            "Dermatology department treats skin conditions. Specialises "
            "in eczema, psoriasis, skin cancer, acne, infections, "
            "and allergic reactions. Performs skin biopsies, "
            "dermoscopy, and phototherapy. Treats hair and nail "
            "conditions."
        )
    },
    {
        "id": "dept_psychiatry",
        "department_name": "Psychiatry",
        "description": (
            "Psychiatry department treats mental health conditions. "
            "Specialises in depression, anxiety, bipolar disorder, "
            "schizophrenia, PTSD, eating disorders, and addiction. "
            "Provides psychiatric assessment, medication management, "
            "and crisis intervention."
        )
    },
    {
        "id": "dept_emergency",
        "department_name": "Emergency Medicine",
        "description": (
            "Emergency Medicine handles acute life-threatening conditions "
            "requiring immediate attention. Treats trauma, stroke, heart "
            "attack, severe infections, respiratory failure, and acute "
            "abdominal emergencies. Available 24 hours for urgent cases."
        )
    },
]

# ── Urgency Guidelines ────────────────────────────────────────
# Clinical criteria for urgency classification
# Used by urgency node to classify Routine/Semi-urgent/Emergency

URGENCY_GUIDELINES = [
    {
        "id": "urgency_emergency",
        "urgency_level": "Emergency",
        "description": (
            "Emergency — requires immediate or same-day specialist "
            "attention. Indicators: severe chest pain with radiation, "
            "sudden onset severe headache, stroke symptoms including "
            "facial drooping and speech difficulty, acute respiratory "
            "distress, signs of sepsis with fever and confusion, "
            "sudden vision loss, acute severe abdominal pain, "
            "suspected pulmonary embolism, acute kidney failure, "
            "diabetic ketoacidosis, suspected meningitis."
        )
    },
    {
        "id": "urgency_semi_urgent",
        "urgency_level": "Semi-urgent",
        "description": (
            "Semi-urgent — requires specialist attention within 48 hours. "
            "Indicators: chest pain that is stable but concerning, "
            "ECG changes requiring investigation, progressive neurological "
            "symptoms, suspected malignancy with rapid progression, "
            "uncontrolled diabetes requiring specialist review, "
            "moderate renal impairment with worsening trend, "
            "suspected DVT without respiratory compromise, "
            "significant unexplained weight loss, new onset seizures "
            "that are now controlled."
        )
    },
    {
        "id": "urgency_routine",
        "urgency_level": "Routine",
        "description": (
            "Routine — stable condition appropriate for scheduled "
            "specialist appointment within 1 to 2 weeks. Indicators: "
            "chronic condition management and review, stable symptoms "
            "requiring specialist opinion, routine follow-up after "
            "previous treatment, preventive care assessment, "
            "non-urgent second opinion, stable diabetes review, "
            "routine thyroid management, chronic pain management, "
            "elective procedure assessment."
        )
    },
]


def ingest_departments() -> bool:
    """
    Loads department descriptions into ChromaDB.
    Creates departments collection if it does not exist.
    Returns True if successful.
    """
    try:
        client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR
        )

        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Delete existing collection if exists — fresh start
        try:
            client.delete_collection("departments")
            logger.info("Deleted existing departments collection")
        except Exception:
            pass

        # Create fresh collection
        collection = client.create_collection(
            name="departments",
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

        # Add all department descriptions
        collection.add(
            ids=[dept["id"] for dept in DEPARTMENT_DESCRIPTIONS],
            documents=[dept["description"] for dept in DEPARTMENT_DESCRIPTIONS],
            metadatas=[
                {"department_name": dept["department_name"]}
                for dept in DEPARTMENT_DESCRIPTIONS
            ]
        )

        logger.info(
            f"Ingested {len(DEPARTMENT_DESCRIPTIONS)} departments "
            f"into ChromaDB"
        )
        return True

    except Exception as e:
        logger.error(f"Department ingestion failed: {e}")
        return False


def ingest_urgency_guidelines() -> bool:
    """
    Loads urgency guidelines into ChromaDB.
    Creates urgency_guidelines collection if not exists.
    Returns True if successful.
    """
    try:
        client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR
        )

        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Delete existing collection if exists
        try:
            client.delete_collection("urgency_guidelines")
            logger.info("Deleted existing urgency_guidelines collection")
        except Exception:
            pass

        # Create fresh collection
        collection = client.create_collection(
            name="urgency_guidelines",
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

        # Add all urgency guidelines
        collection.add(
            ids=[g["id"] for g in URGENCY_GUIDELINES],
            documents=[g["description"] for g in URGENCY_GUIDELINES],
            metadatas=[
                {"urgency_level": g["urgency_level"]}
                for g in URGENCY_GUIDELINES
            ]
        )

        logger.info(
            f"Ingested {len(URGENCY_GUIDELINES)} urgency guidelines "
            f"into ChromaDB"
        )
        return True

    except Exception as e:
        logger.error(f"Urgency guidelines ingestion failed: {e}")
        return False


def run_ingestion() -> bool:
    """
    Runs complete ingestion pipeline.
    Loads departments and urgency guidelines into ChromaDB.
    Called once during setup before processing any documents.
    Returns True if all ingestion successful.
    """
    logger.info("Starting RAG ingestion pipeline")

    dept_success = ingest_departments()
    urgency_success = ingest_urgency_guidelines()

    if dept_success and urgency_success:
        logger.info("RAG ingestion completed successfully")
        return True
    else:
        logger.error("RAG ingestion failed")
        return False


if __name__ == "__main__":
    """
    Run ingestion directly:
    python -m src.rag.ingestion
    """
    import sys
    logging.basicConfig(level=logging.INFO)
    success = run_ingestion()
    sys.exit(0 if success else 1)