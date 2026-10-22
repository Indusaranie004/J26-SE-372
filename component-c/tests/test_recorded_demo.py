
"""
Component C - Recorded Demonstration Tests

Tests:
1. Previously generated Day 1 response
2. Complete Day 2 authority comparison
3. Incomplete authority comparison
4. Missing recorded file
5. Invalid JSON
6. Invalid reasoning response

All tests are offline. No Gemini API calls.
"""

import json

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api import recorded_demo


# ---------------------------------------------
# Test fixtures
# ---------------------------------------------

@pytest.fixture
def client():
    """Create a test HTTP client."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def recorded_file(tmp_path, monkeypatch):
    """
    Replace the real recorded-result path with
    a temporary file during testing.

    This prevents tests from changing actual
    saved reasoning outputs.
    """

    file_path = tmp_path / "recorded_response.json"

    monkeypatch.setattr(
        recorded_demo,
        "RECORDED_RESULT_FILE",
        file_path
    )

    return file_path


def make_test_response():
    """
    Construct a minimal valid reasoning response.

    This contains artificial test content,
    not genuine model-generated analysis.
    """

    return {
        "legal_issue": (
            "Does the fictional permit holder "
            "require prior notice?"
        ),

        "relevant_facts": [
            "The permit was revoked.",
            "No prior notice was given."
        ],

        "authorities": [
            {
                "case_id": "MOCK_SC_001",
                "case_name": "Mock Business Association",
                "court": "Supreme Court",
                "relevance_to_issue": (
                    "Addresses prior notice."
                ),
                "validity_status": "good_law",
                "judicial_treatment_summary": (
                    "Followed by a later fictional case."
                ),
                "authority_assessment": (
                    "Relevant to procedural fairness."
                ),
                "supporting_evidence": [
                    {
                        "case_id": "MOCK_SC_001",
                        "passage_id": "P1"
                    }
                ]
            }
        ],

        "cross_case_analysis": (
            "The supplied authority concerns "
            "procedural fairness."
        ),

        "legislation_considered": [],

        "application": (
            "The fictional facts involve "
            "revocation without notice."
        ),

        "conclusion": (
            "The supplied evidence supports "
            "a notice requirement."
        ),

        "limitations_or_insufficient_evidence": [
            "Only fictional test evidence was supplied."
        ]
    }


def save_test_json(file_path, data):
    """Write a temporary recorded response."""

    file_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )


# ---------------------------------------------
# Test 1 - Day 1 recorded response
# ---------------------------------------------

def test_day1_recorded_response(
    client,
    recorded_file
):
    """
    Older responses without authority_comparison
    should remain compatible.
    """

    save_test_json(
        recorded_file,
        make_test_response()
    )

    response = client.get(
        "/api/reasoning/demo/recorded"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "recorded"

    assert data["comparison_available"] is False

    assert data["result"]["authorities"][0][
        "case_id"
    ] == "MOCK_SC_001"

    assert (
        data["result"]["authority_comparison"][
            "hierarchy_considerations"
        ] is None
    )

    assert "not a live Gemini result" in data["note"]


# ---------------------------------------------
# Test 2 - Complete authority comparison
# ---------------------------------------------

def test_recorded_complete_comparison(
    client,
    recorded_file
):
    """
    A response containing all four comparison
    fields should report comparison_available=True.
    """

    data = make_test_response()

    data["authority_comparison"] = {
        "hierarchy_considerations": (
            "Court hierarchy was considered."
        ),
        "chronology_considerations": (
            "Judgment chronology was considered."
        ),
        "judicial_treatment_considerations": (
            "Judicial treatment was considered."
        ),
        "conflicts_or_distinctions": (
            "Relevant distinctions were considered."
        )
    }

    save_test_json(recorded_file, data)

    response = client.get(
        "/api/reasoning/demo/recorded"
    )

    assert response.status_code == 200

    result = response.json()

    assert result["comparison_available"] is True

    assert (
        result["result"]["authority_comparison"][
            "chronology_considerations"
        ] == "Judgment chronology was considered."
    )


# ---------------------------------------------
# Test 3 - Incomplete authority comparison
# ---------------------------------------------

def test_recorded_incomplete_comparison(
    client,
    recorded_file
):
    """
    A partial comparison must not be reported
    as fully available.
    """

    data = make_test_response()

    data["authority_comparison"] = {
        "hierarchy_considerations": (
            "Court hierarchy was considered."
        )
    }

    save_test_json(recorded_file, data)

    response = client.get(
        "/api/reasoning/demo/recorded"
    )

    assert response.status_code == 200

    assert (
        response.json()["comparison_available"]
        is False
    )


# ---------------------------------------------
# Test 4 - Missing recorded file
# ---------------------------------------------

def test_recorded_file_not_found(
    client,
    recorded_file
):
    """A missing saved result should return 404."""

    assert not recorded_file.exists()

    response = client.get(
        "/api/reasoning/demo/recorded"
    )

    assert response.status_code == 404

    assert (
        "not found"
        in response.json()["detail"].lower()
    )


# ---------------------------------------------
# Test 5 - Invalid JSON
# ---------------------------------------------

def test_recorded_invalid_json(
    client,
    recorded_file
):
    """Malformed JSON should return a clear error."""

    recorded_file.write_text(
        "{ this is not valid JSON",
        encoding="utf-8"
    )

    response = client.get(
        "/api/reasoning/demo/recorded"
    )

    assert response.status_code == 500

    assert (
        "could not be read or validated"
        in response.json()["detail"].lower()
    )


# ---------------------------------------------
# Test 6 - Invalid reasoning structure
# ---------------------------------------------

def test_recorded_invalid_schema(
    client,
    recorded_file
):
    """
    Valid JSON that does not match ReasoningResponse
    should be rejected.
    """

    save_test_json(
        recorded_file,
        {
            "legal_issue": "Test issue",
            "conclusion": "Test conclusion"
        }
    )

    response = client.get(
        "/api/reasoning/demo/recorded"
    )

    assert response.status_code == 500

    assert (
        "could not be read or validated"
        in response.json()["detail"].lower()
    )
