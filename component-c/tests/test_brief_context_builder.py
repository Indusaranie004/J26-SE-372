
"""
Tests for Function 2 Legal Brief Context Builder.

Uses fictional evidence and a synthetic
Function 1 reasoning result.

No Gemini API calls are made.
"""

import json

from brief.input_models import BriefGenerationRequest
from brief.context_builder import build_brief_context

from reasoning.input_models import (
    ReasoningRequest,
    Precedent,
    Passage,
)

from reasoning.output_models import (
    ReasoningResponse,
    AuthorityAnalysis,
)


def make_brief_request():
    """
    Construct a small fictional scenario.
    """

    source_request = ReasoningRequest(
        query="Is prior notice required?",
        case_facts=[
            "A business held a valid permit.",
            "The permit was revoked without notice.",
            "No public safety emergency was identified."
        ],
        precedents=[
            Precedent(
                case_id="MOCK_SC_001",
                passages=[
                    Passage(
                        passage_id="P1",
                        text=(
                            "Reasonable notice is ordinarily "
                            "required before permit revocation."
                        )
                    )
                ]
            )
        ]
    )

    reasoning_result = ReasoningResponse(
        legal_issue="Whether prior notice is required.",
        authorities=[
            AuthorityAnalysis(
                case_id="MOCK_SC_001",
                relevance_to_issue="Directly relevant.",
                judicial_treatment_summary=(
                    "No judicial treatment supplied."
                ),
                authority_assessment=(
                    "Supports ordinary notice requirements."
                ),
            )
        ],
        cross_case_analysis=(
            "The supplied passage supports "
            "ordinary notice requirements."
        ),
        application=(
            "The business received no notice."
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


def test_context_is_valid_json():
    request = make_brief_request()

    context = build_brief_context(request)

    data = json.loads(context)

    assert isinstance(data, dict)
    assert data["requested_title"] == request.title


def test_original_evidence_is_preserved():
    request = make_brief_request()

    data = json.loads(
        build_brief_context(request)
    )

    source = data["source_evidence"]

    assert (
        source["query"]
        == "Is prior notice required?"
    )

    assert len(source["precedents"]) == 1

    assert (
        source["precedents"][0]["case_id"]
        == "MOCK_SC_001"
    )

    assert (
        source["precedents"][0]["passages"][0]["passage_id"]
        == "P1"
    )


def test_case_facts_have_correct_indices():
    request = make_brief_request()

    data = json.loads(
        build_brief_context(request)
    )

    indexed_facts = data["case_facts_indexed"]

    assert len(indexed_facts) == 3

    assert [
        fact["fact_index"]
        for fact in indexed_facts
    ] == [0, 1, 2]

    assert (
        indexed_facts[1]["text"]
        == "The permit was revoked without notice."
    )


def test_function_one_reasoning_is_included():
    request = make_brief_request()

    data = json.loads(
        build_brief_context(request)
    )

    reasoning = data["function_1_reasoning"]

    assert (
        reasoning["conclusion"]
        == "Prior notice is ordinarily required."
    )

    assert (
        reasoning["authorities"][0]["case_id"]
        == "MOCK_SC_001"
    )


def test_evidence_guidance_distinguishes_sources():
    request = make_brief_request()

    data = json.loads(
        build_brief_context(request)
    )

    guidance = " ".join(data["evidence_guidance"])

    assert "original source_evidence" in guidance

    assert "not an independent" in guidance

    assert "fact_index" in guidance


def test_context_builder_is_deterministic():
    request = make_brief_request()

    first = build_brief_context(request)
    second = build_brief_context(request)

    assert first == second
