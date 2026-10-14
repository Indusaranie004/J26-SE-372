
"""
Component C - FastAPI Endpoint Tests

Tests the existing reasoning pipeline through HTTP.

Uses a fake LLM provider so no Gemini API calls
are made during testing.
"""

import json

import pytest

from fastapi.testclient import TestClient

from api.main import app, get_llm_provider

from reasoning.llm_provider import LLMProvider

from scripts.prepare_day2_scenarios import (
    load_original_request
)


# ---------------------------------------------
# Fake LLM provider
# ---------------------------------------------

class FakeLLMProvider(LLMProvider):
    """
    Simulates an LLM response for API testing.

    This provider does not contact Gemini.
    """

    def __init__(self, request, mode="success"):
        self.request = request
        self.mode = mode
        self.call_count = 0

    def generate(self, system_prompt, user_prompt):

        self.call_count += 1

        if self.mode == "provider_failure":
            raise RuntimeError(
                "Simulated provider failure"
            )

        authorities = []

        for precedent in self.request.precedents:

            validity_status = (
                precedent.validity.status
                if precedent.validity
                else "unknown"
            )

            supporting_evidence = [
                {
                    "case_id": precedent.case_id,
                    "passage_id": passage.passage_id
                }
                for passage in precedent.passages
            ]

            authorities.append({
                "case_id": precedent.case_id,
                "case_name": precedent.case_name,
                "court": precedent.court,
                "relevance_to_issue": (
                    "Controlled test relevance."
                ),
                "validity_status": validity_status,
                "judicial_treatment_summary": (
                    "Controlled test treatment summary."
                ),
                "authority_assessment": (
                    "Controlled test assessment."
                ),
                "supporting_evidence": supporting_evidence
            })

        # Intentionally introduce an invalid passage
        # for the grounding-failure test.
        if self.mode == "invalid_grounding":
            authorities[0]["supporting_evidence"][0][
                "passage_id"
            ] = "INVALID_PASSAGE_ID"

        response = {
            "legal_issue": self.request.query,

            "relevant_facts": self.request.case_facts,

            "authorities": authorities,

            "authority_comparison": {
                "hierarchy_considerations": (
                    "Controlled hierarchy test."
                ),
                "chronology_considerations": (
                    "Controlled chronology test."
                ),
                "judicial_treatment_considerations": (
                    "Controlled judicial treatment test."
                ),
                "conflicts_or_distinctions": (
                    "Controlled conflict test."
                )
            },

            "cross_case_analysis": (
                "Controlled cross-case synthesis."
            ),

            "legislation_considered": [],

            "application": (
                "Controlled application to facts."
            ),

            "conclusion": (
                "Controlled test conclusion."
            ),

            "limitations_or_insufficient_evidence": []
        }

        return json.dumps(response)


# ---------------------------------------------
# Fixtures
# ---------------------------------------------

@pytest.fixture
def mock_request():
    return load_original_request()


@pytest.fixture
def client():
    """
    Create an HTTP test client.

    Clear dependency overrides after each test.
    """

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def override_provider(provider):
    """
    Replace Gemini with the test provider.
    """

    app.dependency_overrides[
        get_llm_provider
    ] = lambda: provider


# ---------------------------------------------
# Test 1: Health endpoint
# ---------------------------------------------

def test_health_endpoint(client):

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"

    assert data["component"] == "Component C"


# ---------------------------------------------
# Test 2: Successful reasoning request
# ---------------------------------------------

def test_analyze_success(client, mock_request):

    provider = FakeLLMProvider(mock_request)

    override_provider(provider)

    response = client.post(
        "/api/reasoning/analyze",
        json=mock_request.model_dump(mode="json")
    )

    assert response.status_code == 200

    data = response.json()

    assert provider.call_count == 1

    assert data["legal_issue"] == mock_request.query

    assert len(data["authorities"]) == 3

    assert "authority_comparison" in data

    assert (
        data["authority_comparison"][
            "hierarchy_considerations"
        ] == "Controlled hierarchy test."
    )

    assert data["conclusion"] == (
        "Controlled test conclusion."
    )


# ---------------------------------------------
# Test 3: Invalid input
# ---------------------------------------------

def test_analyze_rejects_empty_precedents(
    client,
    mock_request
):

    provider = FakeLLMProvider(mock_request)

    override_provider(provider)

    invalid_data = mock_request.model_dump(
        mode="json"
    )

    invalid_data["precedents"] = []

    response = client.post(
        "/api/reasoning/analyze",
        json=invalid_data
    )

    assert response.status_code == 422

    assert provider.call_count == 0


# ---------------------------------------------
# Test 4: Grounding validation failure
# ---------------------------------------------

def test_analyze_rejects_invalid_grounding(
    client,
    mock_request
):

    provider = FakeLLMProvider(
        mock_request,
        mode="invalid_grounding"
    )

    override_provider(provider)

    response = client.post(
        "/api/reasoning/analyze",
        json=mock_request.model_dump(mode="json")
    )

    assert response.status_code == 502

    assert (
        "grounding validation"
        in response.json()["detail"].lower()
    )


# ---------------------------------------------
# Test 5: Provider failure
# ---------------------------------------------

def test_analyze_handles_provider_failure(
    client,
    mock_request
):

    provider = FakeLLMProvider(
        mock_request,
        mode="provider_failure"
    )

    override_provider(provider)

    response = client.post(
        "/api/reasoning/analyze",
        json=mock_request.model_dump(mode="json")
    )

    assert response.status_code == 502

    assert (
        "usable reasoning response"
        in response.json()["detail"]
    )
