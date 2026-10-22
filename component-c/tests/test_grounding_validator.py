
"""
Tests for evidence grounding validation.

Uses fictional precedent data to verify that
unsupported case IDs, passages and validity
statuses are detected.
"""

from pathlib import Path

import pytest

from reasoning.input_models import ReasoningRequest
from reasoning.output_models import ReasoningResponse
from reasoning.grounding_validator import validate_grounding


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "reasoning"
    / "data"
    / "mock_case_data.json"
)


@pytest.fixture
def reasoning_request():
    """Load the controlled fictional precedent dataset."""

    return ReasoningRequest.model_validate_json(
        DATA_FILE.read_text(encoding="utf-8")
    )


@pytest.fixture
def valid_response(reasoning_request):
    """Build a valid reasoning response for testing."""

    authorities = []

    for precedent in reasoning_request.precedents:

        authorities.append({
            "case_id": precedent.case_id,
            "case_name": precedent.case_name,
            "court": precedent.court,
            "relevance_to_issue": "Relevant to the legal question.",
            "validity_status": precedent.validity.status,
            "judicial_treatment_summary": "Treatment considered.",
            "authority_assessment": "Assessment based on supplied evidence.",
            "supporting_evidence": [
                {
                    "case_id": precedent.case_id,
                    "passage_id": passage.passage_id
                }
                for passage in precedent.passages
            ]
        })

    return ReasoningResponse.model_validate({
        "legal_issue": reasoning_request.query,
        "relevant_facts": reasoning_request.case_facts,
        "authorities": authorities,
        "cross_case_analysis": "Comparison of supplied authorities.",
        "legislation_considered": [],
        "application": "Application to the supplied facts.",
        "conclusion": "Test conclusion.",
        "limitations_or_insufficient_evidence": []
    })


def test_valid_grounding(reasoning_request, valid_response):
    """Valid case and passage references should pass."""

    errors = validate_grounding(reasoning_request, valid_response)

    assert errors == []


def test_invented_passage_detected(reasoning_request, valid_response):
    """A fabricated passage ID must be detected."""

    valid_response.authorities[0].supporting_evidence[0].passage_id = (
        "P999"
    )

    errors = validate_grounding(reasoning_request, valid_response)

    assert any("Unknown passage" in error for error in errors)


def test_incorrect_validity_detected(reasoning_request, valid_response):
    """Incorrect precedent validity must be detected."""

    valid_response.authorities[2].validity_status = "good_law"

    errors = validate_grounding(reasoning_request, valid_response)

    assert any("Validity mismatch" in error for error in errors)


def test_missing_authority_detected(reasoning_request, valid_response):
    """The model must not silently omit a supplied authority."""

    valid_response.authorities.pop()

    errors = validate_grounding(reasoning_request, valid_response)

    assert any("Missing authority" in error for error in errors)


def test_duplicate_authority_detected(reasoning_request, valid_response):
    """Duplicate authority assessments must be detected."""

    duplicate = valid_response.authorities[0].model_copy(deep=True)

    valid_response.authorities.append(duplicate)

    errors = validate_grounding(reasoning_request, valid_response)

    assert any("Duplicate authority" in error for error in errors)
