
"""
Component C - Function 2
FastAPI Endpoint Tests

Tests:
- Recorded legal brief endpoint
- Readable legal brief endpoint
- Live generation endpoint with a fake provider
- Request validation
- Grounding failure handling
- Provider error handling
- Swagger route registration

No Gemini API calls are made.
"""

import json

from pathlib import Path

import pytest

from fastapi.testclient import TestClient

import api.brief_api as brief_api

from api.main import app

from api.brief_api import (
    get_brief_provider,
)

from reasoning.input_models import (
    ReasoningRequest,
    Precedent,
    Passage,
)

from reasoning.output_models import (
    ReasoningResponse,
    AuthorityAnalysis,
)

from brief.input_models import (
    BriefGenerationRequest,
)

from brief.output_models import (
    BriefEvidenceReference,
    BriefClaim,
    LegalBrief,
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
# Fake provider
# ---------------------------------------------

class FakeBriefProvider:
    """
    Returns a predefined result instead
    of calling Gemini.
    """

    def __init__(
        self,
        response: str | None = None,
        error: Exception | None = None,
    ):

        self.response = response
        self.error = error

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

        if self.error is not None:
            raise self.error

        return self.response


def inject_provider(provider):
    """
    Replace the real Function 2 Gemini
    dependency during tests.
    """

    app.dependency_overrides[get_brief_provider] = (
        lambda: provider
    )


# ---------------------------------------------
# Fictional test input
# ---------------------------------------------

def make_request():

    source = ReasoningRequest(
        query="Is prior notice required?",

        case_facts=[
            "A permit was revoked without notice."
        ],

        precedents=[
            Precedent(
                case_id="MOCK_SC_001",

                passages=[
                    Passage(
                        passage_id="P1",
                        text="Prior notice is required."
                    )
                ]
            )
        ]
    )

    reasoning = ReasoningResponse(
        legal_issue="Whether notice is required.",

        authorities=[
            AuthorityAnalysis(
                case_id="MOCK_SC_001",
                relevance_to_issue="Directly relevant.",
                judicial_treatment_summary=(
                    "No treatment supplied."
                ),
                authority_assessment=(
                    "Supports prior notice."
                ),
            )
        ],

        cross_case_analysis=(
            "The supplied authority supports notice."
        ),

        application=(
            "The permit was revoked without notice."
        ),

        conclusion=(
            "Prior notice is ordinarily required."
        ),
    )

    return BriefGenerationRequest(
        source_request=source,
        reasoning_result=reasoning,
        title="Permit Revocation Research Brief"
    )


def make_valid_brief():

    return LegalBrief(
        title="Permit Revocation Research Brief",

        legal_issue="Whether notice is required.",

        legal_analysis=[
            BriefClaim(
                claim_id="CLAIM_001",

                statement="Prior notice is required.",

                support_status="supported",

                evidence_references=[
                    BriefEvidenceReference(
                        source_type="case_passage",
                        case_id="MOCK_SC_001",
                        passage_id="P1"
                    )
                ]
            )
        ],

        conclusion=[
            BriefClaim(
                claim_id="CLAIM_002",

                statement=(
                    "The permit was revoked without notice."
                ),

                support_status="supported",

                evidence_references=[
                    BriefEvidenceReference(
                        source_type="case_fact",
                        fact_index=0
                    )
                ]
            )
        ]
    )


# ---------------------------------------------
# Recorded demo tests
# ---------------------------------------------

def test_recorded_brief_endpoint(client):

    response = client.get(
        "/api/brief/demo/recorded"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["mode"] == "recorded"

    assert body["result"]["document_type"] == (
        "research_brief"
    )

    assert len(
        body["result"]["legal_analysis"]
    ) == 3

    assert len(
        body["result"]["conclusion"]
    ) == 2


def test_readable_brief_endpoint(client):

    response = client.get(
        "/api/brief/demo/readable"
    )

    assert response.status_code == 200

    assert "text/markdown" in response.headers[
        "content-type"
    ]

    assert "DEMONSTRATION MODE: RECORDED" in (
        response.text
    )

    assert "## Legal Issue" in response.text

    assert "CLAIM_023" in response.text


def test_missing_recorded_file_returns_404(
    client,
    monkeypatch,
    tmp_path,
):

    missing_file = tmp_path / "missing_brief.json"

    monkeypatch.setattr(
        brief_api,
        "RECORDED_BRIEF_FILE",
        missing_file,
    )

    response = client.get(
        "/api/brief/demo/recorded"
    )

    assert response.status_code == 404


def test_invalid_recorded_file_returns_500(
    client,
    monkeypatch,
    tmp_path,
):

    invalid_file = tmp_path / "invalid_brief.json"

    invalid_file.write_text(
        '{"invalid": true}',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        brief_api,
        "RECORDED_BRIEF_FILE",
        invalid_file,
    )

    response = client.get(
        "/api/brief/demo/recorded"
    )

    assert response.status_code == 500


# ---------------------------------------------
# Live generation tests - fake provider
# ---------------------------------------------

def test_generate_brief_success(client):

    provider = FakeBriefProvider(
        response=make_valid_brief().model_dump_json()
    )

    inject_provider(provider)

    request = make_request()

    response = client.post(
        "/api/brief/generate",
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == request.title

    assert body["document_type"] == "research_brief"

    assert provider.call_count == 1

    assert "source_evidence" in (
        provider.last_user_prompt
    )

    assert "function_1_reasoning" in (
        provider.last_user_prompt
    )


def test_invalid_request_returns_422(client):

    inject_provider(
        FakeBriefProvider(
            response=make_valid_brief().model_dump_json()
        )
    )

    response = client.post(
        "/api/brief/generate",
        json={"invalid_input": True},
    )

    assert response.status_code == 422


def test_wrong_generated_title_returns_502(client):

    payload = make_valid_brief().model_dump(
        mode="json"
    )

    payload["title"] = "Unexpected Brief Title"

    inject_provider(
        FakeBriefProvider(
            response=json.dumps(payload)
        )
    )

    response = client.post(
        "/api/brief/generate",
        json=make_request().model_dump(mode="json"),
    )

    assert response.status_code == 502


def test_invalid_grounding_returns_502(client):

    payload = make_valid_brief().model_dump(
        mode="json"
    )

    payload["legal_analysis"][0][
        "evidence_references"
    ][0]["passage_id"] = "NONEXISTENT_PASSAGE"

    inject_provider(
        FakeBriefProvider(
            response=json.dumps(payload)
        )
    )

    response = client.post(
        "/api/brief/generate",
        json=make_request().model_dump(mode="json"),
    )

    assert response.status_code == 502

    assert "validation" in (
        response.json()["detail"].lower()
    )


def test_invalid_generated_schema_returns_502(client):

    inject_provider(
        FakeBriefProvider(
            response='{"invalid": true}'
        )
    )

    response = client.post(
        "/api/brief/generate",
        json=make_request().model_dump(mode="json"),
    )

    assert response.status_code == 502


def test_provider_runtime_error_returns_502(client):

    inject_provider(
        FakeBriefProvider(
            error=RuntimeError(
                "Fake provider returned empty output."
            )
        )
    )

    response = client.post(
        "/api/brief/generate",
        json=make_request().model_dump(mode="json"),
    )

    assert response.status_code == 502

    assert "usable legal brief" in (
        response.json()["detail"]
    )


# ---------------------------------------------
# Swagger and Function 1 compatibility
# ---------------------------------------------

def test_new_routes_appear_in_openapi(client):

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/brief/generate" in paths

    assert "/api/brief/demo/recorded" in paths

    assert "/api/brief/demo/readable" in paths

    # Function 1 remains available
    assert "/api/reasoning/analyze" in paths

    assert "/health" in paths

    assert client.get("/health").status_code == 200

def test_recorded_brief_uses_improved_treatment_references(
    client
):
    """
    Verify that the recorded PP1 demonstration
    uses the improved judicial-treatment citations.
    """

    response = client.get(
        "/api/brief/demo/recorded"
    )

    assert response.status_code == 200

    brief = response.json()["result"]

    treatment_claims = brief["precedent_treatment"]

    assert treatment_claims

    for claim in treatment_claims:

        reference_types = {
            reference["source_type"]
            for reference in claim["evidence_references"]
        }

        assert "judicial_treatment" in reference_types