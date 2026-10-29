
"""
Component C - Full Component B Pipeline Tests

Tests Component B -> Function 1 -> Function 2
using deterministic fake providers.

No live Gemini calls are made.
"""

import json

import pytest

from fastapi.testclient import TestClient

from api.main import (
    app,
    get_llm_provider,
)

from api.brief_api import (
    get_brief_provider,
)

from reasoning.output_models import (
    AuthorityAnalysis,
    ReasoningResponse,
)

from brief.output_models import (
    BriefClaim,
    BriefEvidenceReference,
    LegalBrief,
)


ENDPOINT = "/api/integration/component-b/brief"

DEFAULT_TITLE = (
    "Component B Metadata Legal Research Brief"
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
# Fake LLM provider
# ---------------------------------------------

class FakeProvider:

    def __init__(self, response: str):

        self.response = response
        self.call_count = 0
        self.last_user_prompt = None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        self.call_count += 1

        self.last_user_prompt = user_prompt

        return self.response


# ---------------------------------------------
# Component B test input
# ---------------------------------------------

def make_payload():

    return {
        "query": (
            "What can be determined from "
            "the supplied citation relationships?"
        ),
        "case_facts": [
            "A dispute requires preliminary "
            "precedent research."
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
                "cited_by": [],
                "legislation": [
                    {
                        "act_id": "leg_001",
                        "name": "Civil Procedure Code",
                        "section": "s.5",
                    }
                ],
                "appeal_chain": [],
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
# Function 1 fake output
# ---------------------------------------------

def make_reasoning():

    return ReasoningResponse(
        legal_issue=(
            "Preliminary analysis of "
            "available citation relationships."
        ),
        authorities=[
            AuthorityAnalysis(
                case_id="case_001",
                relevance_to_issue=(
                    "Retrieved by Component B."
                ),
                validity_status="unknown",
                judicial_treatment_summary=(
                    "case_001 followed case_002."
                ),
                authority_assessment=(
                    "The graph relationship is supplied, "
                    "but the judgment text is missing."
                ),
            ),
            AuthorityAnalysis(
                case_id="case_002",
                relevance_to_issue=(
                    "Retrieved by Component B."
                ),
                validity_status="unknown",
                judicial_treatment_summary=(
                    "Referenced by case_001."
                ),
                authority_assessment=(
                    "The underlying legal holding "
                    "cannot be determined."
                ),
            ),
        ],
        cross_case_analysis=(
            "The available records identify "
            "citation relationships, not the "
            "complete legal propositions."
        ),
        application=(
            "Insufficient judgment text is "
            "available for a definitive application."
        ),
        conclusion=(
            "The legal issue cannot be conclusively "
            "resolved from metadata alone."
        ),
        limitations_or_insufficient_evidence=[
            "Judgment text is unavailable."
        ],
    )


# ---------------------------------------------
# Function 2 fake output
# ---------------------------------------------

def make_brief(
    title=DEFAULT_TITLE,
):

    return LegalBrief(
        title=title,
        legal_issue=(
            "Preliminary analysis of citation metadata."
        ),
        legal_analysis=[
            BriefClaim(
                claim_id="CLAIM_001",
                statement=(
                    "The supplied graph records "
                    "case_001 following case_002."
                ),
                support_status="supported",
                evidence_references=[
                    BriefEvidenceReference(
                        source_type="judicial_treatment",
                        source_case_id="case_001",
                        target_case_id="case_002",
                        treatment_status="followed",
                        scope="ratio",
                    )
                ],
            )
        ],
        conclusion=[
            BriefClaim(
                claim_id="CLAIM_002",
                statement=(
                    "The substantive legal issue "
                    "cannot be resolved without "
                    "judgment text."
                ),
                support_status="insufficient_evidence",
            )
        ],
        limitations=[
            "Statutory wording is unavailable."
        ],
    )


# ---------------------------------------------
# Dependency overrides
# ---------------------------------------------

def install_providers(
    reasoning_response: str,
    brief_response: str,
):

    reasoning_provider = FakeProvider(
        reasoning_response
    )

    brief_provider = FakeProvider(
        brief_response
    )

    app.dependency_overrides[get_llm_provider] = (
        lambda: reasoning_provider
    )

    app.dependency_overrides[get_brief_provider] = (
        lambda: brief_provider
    )

    return reasoning_provider, brief_provider


# ---------------------------------------------
# Tests
# ---------------------------------------------

def test_full_pipeline_route_registered(client):

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert ENDPOINT in paths

    assert "/api/reasoning/analyze" in paths

    assert "/api/brief/generate" in paths


def test_full_pipeline_success(client):

    reasoning_provider, brief_provider = (
        install_providers(
            make_reasoning().model_dump_json(),
            make_brief().model_dump_json(),
        )
    )

    response = client.post(
        ENDPOINT,
        json=make_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["evidence_mode"] == "metadata_only"

    assert body["reasoning"]["authorities"]

    assert body["legal_brief"]["legal_analysis"]

    assert body["legal_brief"]["conclusion"]

    assert reasoning_provider.call_count == 1

    assert brief_provider.call_count == 1

    assert "case_001" in (
        reasoning_provider.last_user_prompt
    )

    assert "function_1_reasoning" in (
        brief_provider.last_user_prompt
    )

    assert "case_001" in (
        brief_provider.last_user_prompt
    )

    assert any(
        "Judgment passage text" in item
        for item in body["legal_brief"]["limitations"]
    )

    assert any(
        "Judgment passage text" in item
        for item in body["reasoning"][
            "limitations_or_insufficient_evidence"
        ]
    )


def test_full_pipeline_duplicate_seed_rejected(client):

    reasoning_provider, brief_provider = (
        install_providers(
            make_reasoning().model_dump_json(),
            make_brief().model_dump_json(),
        )
    )

    payload = make_payload()

    payload["clusters"].append(
        payload["clusters"][0].copy()
    )

    response = client.post(
        ENDPOINT,
        json=payload,
    )

    assert response.status_code == 422

    assert reasoning_provider.call_count == 0

    assert brief_provider.call_count == 0


def test_full_pipeline_stops_if_reasoning_fails(client):

    reasoning_provider, brief_provider = (
        install_providers(
            '{"invalid": true}',
            make_brief().model_dump_json(),
        )
    )

    response = client.post(
        ENDPOINT,
        json=make_payload(),
    )

    assert response.status_code == 502

    assert reasoning_provider.call_count == 1

    assert brief_provider.call_count == 0


def test_full_pipeline_rejects_invalid_brief(client):

    reasoning_provider, brief_provider = (
        install_providers(
            make_reasoning().model_dump_json(),
            '{"invalid": true}',
        )
    )

    response = client.post(
        ENDPOINT,
        json=make_payload(),
    )

    assert response.status_code == 502

    assert reasoning_provider.call_count == 1

    assert brief_provider.call_count == 1


def test_full_pipeline_accepts_custom_title(client):

    title = "Custom Metadata Research Brief"

    reasoning_provider, brief_provider = (
        install_providers(
            make_reasoning().model_dump_json(),
            make_brief(title=title).model_dump_json(),
        )
    )

    response = client.post(
        ENDPOINT,
        params={"title": title},
        json=make_payload(),
    )

    assert response.status_code == 200

    assert (
        response.json()["legal_brief"]["title"]
        == title
    )

    assert reasoning_provider.call_count == 1

    assert brief_provider.call_count == 1
