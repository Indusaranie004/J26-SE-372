
"""
Tests for Function 2 Legal Brief Generation Service.

Uses a fake LLM provider.

No real Gemini API requests are made.
"""

import json

import pytest
from pydantic import ValidationError

from reasoning.llm_provider import LLMProvider

from reasoning.input_models import (
    ReasoningRequest,
    Precedent,
    Passage,
)

from reasoning.output_models import (
    ReasoningResponse,
    AuthorityAnalysis,
)

from brief.input_models import BriefGenerationRequest
from brief.output_models import (
    BriefClaim,
    BriefEvidenceReference,
    LegalBrief,
)

from brief.brief_service import (
    run_legal_brief_generation
)

from brief.brief_prompt import (
    LEGAL_BRIEF_SYSTEM_PROMPT
)


class FakeBriefProvider(LLMProvider):
    """
    Returns a predetermined JSON response
    instead of calling Gemini.
    """

    def __init__(self, response: str):
        self.response = response
        self.last_system_prompt = None
        self.last_user_prompt = None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:

        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt

        return self.response


def make_brief_request():
    source_request = ReasoningRequest(
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

    reasoning_result = ReasoningResponse(
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
            "The supplied evidence supports notice."
        ),
        application=(
            "The permit was revoked without notice."
        ),
        conclusion=(
            "Prior notice is ordinarily required."
        )
    )

    return BriefGenerationRequest(
        source_request=source_request,
        reasoning_result=reasoning_result,
        title="Permit Revocation Research Brief"
    )


def make_valid_brief():
    evidence = BriefEvidenceReference(
        source_type="case_passage",
        case_id="MOCK_SC_001",
        passage_id="P1"
    )

    claim = BriefClaim(
        claim_id="CLAIM_001",
        statement="Prior notice is required.",
        support_status="supported",
        evidence_references=[evidence]
    )

    conclusion = BriefClaim(
        claim_id="CLAIM_002",
        statement="The permit revocation lacked notice.",
        support_status="supported",
        evidence_references=[
            BriefEvidenceReference(
                source_type="case_fact",
                fact_index=0
            )
        ]
    )

    return LegalBrief(
        title="Permit Revocation Research Brief",
        legal_issue="Whether prior notice is required.",
        legal_analysis=[claim],
        conclusion=[conclusion]
    )


def test_brief_generation_returns_legal_brief():
    request = make_brief_request()

    provider = FakeBriefProvider(
        make_valid_brief().model_dump_json()
    )

    result = run_legal_brief_generation(
        request,
        provider
    )

    assert isinstance(result, LegalBrief)
    assert result.title == request.title
    assert len(result.legal_analysis) == 1


def test_brief_generation_uses_drafting_prompt():
    request = make_brief_request()

    provider = FakeBriefProvider(
        make_valid_brief().model_dump_json()
    )

    run_legal_brief_generation(
        request,
        provider
    )

    assert (
        provider.last_system_prompt
        == LEGAL_BRIEF_SYSTEM_PROMPT
    )

    assert "Function 1" in provider.last_system_prompt


def test_brief_generation_includes_original_evidence():
    request = make_brief_request()

    provider = FakeBriefProvider(
        make_valid_brief().model_dump_json()
    )

    run_legal_brief_generation(
        request,
        provider
    )

    context = json.loads(provider.last_user_prompt)

    assert "source_evidence" in context
    assert "function_1_reasoning" in context

    assert (
        context["source_evidence"]["precedents"][0]["case_id"]
        == "MOCK_SC_001"
    )


def test_invalid_llm_json_is_rejected():
    request = make_brief_request()

    provider = FakeBriefProvider(
        '{"invalid": true}'
    )

    with pytest.raises(ValidationError):
        run_legal_brief_generation(
            request,
            provider
        )


def test_supported_claim_without_evidence_is_rejected():
    request = make_brief_request()

    payload = make_valid_brief().model_dump(
        mode="json"
    )

    payload["legal_analysis"][0]["evidence_references"] = []

    provider = FakeBriefProvider(
        json.dumps(payload)
    )

    with pytest.raises(ValidationError):
        run_legal_brief_generation(
            request,
            provider
        )


def test_wrong_document_title_is_rejected():
    request = make_brief_request()

    payload = make_valid_brief().model_dump(
        mode="json"
    )

    payload["title"] = "An Unexpected Title"

    provider = FakeBriefProvider(
        json.dumps(payload)
    )

    with pytest.raises(
        ValueError,
        match="does not match the requested title"
    ):
        run_legal_brief_generation(
            request,
            provider
        )
