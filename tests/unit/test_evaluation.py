# ============================================================
# Unit Tests — Ragas Evaluation Pipeline
# Tests evaluation runs correctly
# Tests accuracy calculations
# Tests dataset validation
# ============================================================

import pytest
import os
from unittest.mock import patch


def test_golden_dataset_not_empty():
    """
    Golden dataset must have documents.
    Empty dataset produces meaningless results.
    """
    from src.evaluation.ragas_eval import GOLDEN_DATASET
    assert len(GOLDEN_DATASET) > 0


def test_golden_dataset_minimum_size():
    """
    Golden dataset must have at least 10 documents.
    Minimum for statistically meaningful evaluation.
    """
    from src.evaluation.ragas_eval import GOLDEN_DATASET
    assert len(GOLDEN_DATASET) >= 10


def test_all_documents_have_required_fields():
    """
    Every golden dataset document has all required fields.
    Missing fields cause silent evaluation errors.
    """
    from src.evaluation.ragas_eval import GOLDEN_DATASET

    required_fields = [
        "document_id",
        "document_text",
        "expected_department",
        "expected_urgency"
    ]

    for item in GOLDEN_DATASET:
        for field in required_fields:
            assert field in item, (
                f"Document {item.get('document_id', 'unknown')} "
                f"missing required field: {field}"
            )


def test_urgency_labels_are_valid():
    """
    All urgency labels must be one of three valid values.
    Invalid labels cause incorrect accuracy calculations.
    """
    from src.evaluation.ragas_eval import GOLDEN_DATASET

    valid_urgency = {"Routine", "Semi-urgent", "Emergency"}

    for item in GOLDEN_DATASET:
        assert item["expected_urgency"] in valid_urgency, (
            f"Document {item['document_id']} has invalid urgency: "
            f"{item['expected_urgency']}"
        )


def test_document_ids_are_unique():
    """
    All document IDs must be unique.
    Duplicate IDs cause incorrect tracking.
    """
    from src.evaluation.ragas_eval import GOLDEN_DATASET

    ids = [item["document_id"] for item in GOLDEN_DATASET]
    assert len(ids) == len(set(ids)), "Duplicate document IDs found"


def test_all_urgency_levels_represented():
    """
    Golden dataset must include all three urgency levels.
    Missing levels means we cannot evaluate that category.
    """
    from src.evaluation.ragas_eval import GOLDEN_DATASET

    urgency_levels = {item["expected_urgency"] for item in GOLDEN_DATASET}
    assert "Emergency" in urgency_levels, "No Emergency cases in dataset"
    assert "Semi-urgent" in urgency_levels, "No Semi-urgent cases in dataset"
    assert "Routine" in urgency_levels, "No Routine cases in dataset"


def test_run_evaluation_returns_correct_structure():
    """
    run_evaluation returns dict with required keys.
    """
    with patch.dict(os.environ, {
        "GCP_PROJECT_ID": "test-project",
        "LANGSMITH_API_KEY": "test-key"
    }):
        from src.evaluation.ragas_eval import run_evaluation
        results = run_evaluation()

        assert "total_documents" in results
        assert "routing_correct" in results
        assert "routing_accuracy" in results
        assert "urgency_correct" in results
        assert "urgency_accuracy" in results
        assert "results" in results


def test_accuracy_values_between_zero_and_one():
    """
    Accuracy values must be between 0.0 and 1.0.
    Values outside this range indicate calculation errors.
    """
    with patch.dict(os.environ, {
        "GCP_PROJECT_ID": "test-project",
        "LANGSMITH_API_KEY": "test-key"
    }):
        from src.evaluation.ragas_eval import run_evaluation
        results = run_evaluation()

        assert 0.0 <= results["routing_accuracy"] <= 1.0
        assert 0.0 <= results["urgency_accuracy"] <= 1.0


def test_total_documents_matches_dataset():
    """
    Total documents in results matches golden dataset size.
    """
    with patch.dict(os.environ, {
        "GCP_PROJECT_ID": "test-project",
        "LANGSMITH_API_KEY": "test-key"
    }):
        from src.evaluation.ragas_eval import run_evaluation
        from src.evaluation.ragas_eval import GOLDEN_DATASET
        results = run_evaluation()

        assert results["total_documents"] == len(GOLDEN_DATASET)