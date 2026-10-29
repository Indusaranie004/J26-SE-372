
"""
Component C - Component B API Integration Tests

Tests:
- Component B route registration
- Metadata-only reasoning integration
- Duplicate seed rejection
- Empty clusters rejection
- Invalid treatment status rejection
- Fabricated passage reference rejection

Uses a fake LLM provider.
No Gemini API calls are made.
"""

import json

import pytest

from fastapi.testclient import TestClient

from api.main import (
    app,
    get_llm_provider,
)

from reasoning.output_models import (
    AuthorityAnalysis,
    ReasoningResponse,
)


# ---------------------------------------------
# Test client
# ---------------------------------------------

@pytest.fixture
def client():

    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ---------------------------------------------
# Fake Function 1 provider
# ---------------------------------------------

class FakeReasoningProvider:

    def __init__(self, response: str):

        self.response = response
        self.call_count = 0
        self.last_system_prompt = None
        self.last_user_prompt = None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt

        return self.response


# ---------------------------------------------
# Sample Component B request
# ---------------------------------------------

def make_component_b_payload():

    return {
        "query": (
            "What can be determined from the "
            "supplied precedent relationships?"
        ),
        "case_facts": [
            "A legal dispute requires analysis "
            "of the retrieved precedents."
        ],
        "reference_date": None,
        "clusters": [
            {
                "seed_id": "case_001",
                "rrf_score": 0.5,
                "cases_cited": [
                    {
                        "target_id": "case_002",
                        "citation_type": "followed",
                        "evidence": "para 12",
                        "scope": "ratio",
                    }
                ],
                "cited_by": [
                    {
                        "target_id": "case_004",
                        "citation_type": "followed",
                        "evidence": "para 3",
                        "scope": None,
                    }
                ],
                "legislation": [
                    {
                        "act_id": "leg_001",
                        "name": "Civil Procedure Code",
                        "section": "s.5",
                    }
                ],
                "appeal_chain": [
                    {
                        "related_id": "case_005",
                        "hops": 1,
                    }
                ],
            },
            {
                "seed_id": "case_002",
                "rrf_score": 0.3,
                "cases_cited": [],
                "cited_by": [],
                "legislation": [],
                "appeal_chain": [],
            },
        ],
    }


# ---------------------------------------------
# Fake reasoning output
# ---------------------------------------------

def make_reasoning_response():

    return ReasoningResponse(
        legal_issue=(
            "Assessment of the supplied "
            "precedent relationships."
        ),
        authorities=[
            AuthorityAnalysis(
                case_id="case_001",
                relevance_to_issue=(
                    "Retrieved as a relevant "
                    "precedent cluster."
                ),
                validity_status="unknown",
                judicial_treatment_summary=(
                    "The supplied graph identifies "
                    "outgoing and incoming citations."
                ),
                authority_assessment=(
                    "The substantive holding cannot "
                    "be verified without judgment text."
                ),
            ),
            AuthorityAnalysis(
                case_id="case_002",
                relevance_to_issue=(
                    "Identified through Component B "
                    "retrieval metadata."
                ),
                validity_status="unknown",
                judicial_treatment_summary=(
                    "The supplied graph identifies "
                    "a followed relationship."
                ),
                authority_assessment=(
                    "The substantive holding cannot "
                    "be verified without judgment text."
                ),
            ),
        ],
        cross_case_analysis=(
            "The supplied graph records relationships "
            "between cases, but does not provide "
            "judgment passages establishing the "
            "underlying legal principles."
        ),
        application=(
            "The available metadata is insufficient "
            "to apply a substantive legal rule "
            "to the facts conclusively."
        ),
        conclusion=(
            "A definitive legal conclusion cannot "
            "be established from these records alone."
        ),
        limitations_or_insufficient_evidence=[
            "Judgment passage text is unavailable.",
            "Statutory wording is unavailable.",
        ],
    )


def install_fake_provider(
    response: str,
) -> FakeReasoningProvider:

    provider = FakeReasoningProvider(response)

    app.dependency_overrides[get_llm_provider] = (
        lambda: provider
    )

    return provider


# ---------------------------------------------
# Tests
# ---------------------------------------------

def test_component_b_route_appears_in_swagger(
    client,
):

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert (
        "/api/integration/component-b/reasoning"
        in paths
    )

    # Existing functionality must remain available.
    assert "/api/reasoning/analyze" in paths
    assert "/api/brief/generate" in paths


def test_component_b_metadata_reasoning_success(
    client,
):

    reasoning = make_reasoning_response()

    provider = install_fake_provider(
        reasoning.model_dump_json()
    )

    response = client.post(
        "/api/integration/component-b/reasoning",
        json=make_component_b_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["authorities"]) == 2

    assert {
        authority["case_id"]
        for authority in body["authorities"]
    } == {"case_001", "case_002"}

    assert provider.call_count == 1

    # Confirms that Component B data reached
    # the actual Function 1 context builder.
    assert "case_001" in provider.last_user_prompt
    assert "case_002" in provider.last_user_prompt


def test_component_b_duplicate_seeds_return_422(
    client,
):

    provider = install_fake_provider(
        make_reasoning_response().model_dump_json()
    )

    payload = make_component_b_payload()

    payload["clusters"].append(
        payload["clusters"][0].copy()
    )

    response = client.post(
        "/api/integration/component-b/reasoning",
        json=payload,
    )

    assert response.status_code == 422
    assert provider.call_count == 0


def test_component_b_empty_clusters_return_422(
    client,
):

    provider = install_fake_provider(
        make_reasoning_response().model_dump_json()
    )

    payload = make_component_b_payload()

    payload["clusters"] = []

    response = client.post(
        "/api/integration/component-b/reasoning",
        json=payload,
    )

    assert response.status_code == 422
    assert provider.call_count == 0


def test_component_b_invalid_treatment_returns_422(
    client,
):

    provider = install_fake_provider(
        make_reasoning_response().model_dump_json()
    )

    payload = make_component_b_payload()

    payload["clusters"][0]["cases_cited"][0][
        "citation_type"
    ] = "invented_treatment_status"

    response = client.post(
        "/api/integration/component-b/reasoning",
        json=payload,
    )

    assert response.status_code == 422
    assert provider.call_count == 0


def test_component_b_fake_passage_is_rejected(
    client,
):

    # The input contains no judgment passages.
    # A generated passage reference must fail
    # grounding validation.

    reasoning = make_reasoning_response().model_dump(
        mode="json"
    )

    reasoning["authorities"][0][
        "supporting_evidence"
    ] = [
        {
            "case_id": "case_001",
            "passage_id": "FAKE_PASSAGE_001",
        }
    ]

    provider = install_fake_provider(
        json.dumps(reasoning)
    )

    response = client.post(
        "/api/integration/component-b/reasoning",
        json=make_component_b_payload(),
    )

    assert response.status_code == 502
    assert provider.call_count == 1
