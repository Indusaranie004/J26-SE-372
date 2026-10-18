
"""
Tests for Component C - Function 2 models.

These tests do not call Gemini.
"""

import pytest
from pydantic import ValidationError

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
    BriefEvidenceReference,
    BriefClaim,
    LegalBrief,
)


def make_source_request():
    return ReasoningRequest(
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


def make_reasoning_result():
    return ReasoningResponse(
        legal_issue="Whether prior notice is required.",
        authorities=[
            AuthorityAnalysis(
                case_id="MOCK_SC_001",
                relevance_to_issue="Directly relevant.",
                judicial_treatment_summary="No treatment supplied.",
                authority_assessment="Relevant to notice.",
            )
        ],
        cross_case_analysis="Notice requirements considered.",
        application="Notice was not provided.",
        conclusion="Notice is required."
    )


def make_supported_claim(claim_id="CLAIM_001"):
    return BriefClaim(
        claim_id=claim_id,
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


def test_input_reuses_function_one_models():
    request = BriefGenerationRequest(
        source_request=make_source_request(),
        reasoning_result=make_reasoning_result()
    )

    assert request.title == "Legal Research Brief"
    assert request.source_request.query
    assert request.reasoning_result.conclusion


def test_input_requires_reasoning_result():
    with pytest.raises(ValidationError):
        BriefGenerationRequest(
            source_request=make_source_request()
        )


def test_case_passage_reference_is_valid():
    reference = BriefEvidenceReference(
        source_type="case_passage",
        case_id="MOCK_SC_001",
        passage_id="P1"
    )

    assert reference.passage_id == "P1"


def test_legislation_reference_is_valid():
    reference = BriefEvidenceReference(
        source_type="legislation",
        act_id="MOCK_ACT_001",
        section="10"
    )

    assert reference.source_type == "legislation"


def test_case_fact_reference_is_valid():
    reference = BriefEvidenceReference(
        source_type="case_fact",
        fact_index=0
    )

    assert reference.fact_index == 0


def test_case_passage_requires_identifiers():
    with pytest.raises(ValidationError):
        BriefEvidenceReference(
            source_type="case_passage",
            case_id="MOCK_SC_001"
        )


def test_supported_claim_requires_evidence():
    with pytest.raises(ValidationError):
        BriefClaim(
            claim_id="CLAIM_001",
            statement="Prior notice is required.",
            support_status="supported"
        )


def test_insufficient_evidence_claim_is_allowed():
    claim = BriefClaim(
        claim_id="CLAIM_002",
        statement=(
            "The supplied evidence does not establish "
            "an entitlement to compensation."
        ),
        support_status="insufficient_evidence"
    )

    assert claim.evidence_references == []


def test_complete_brief_structure():
    brief = LegalBrief(
        title="Permit Revocation Brief",
        legal_issue="Whether prior notice is required.",
        legal_analysis=[
            make_supported_claim("CLAIM_001")
        ],
        conclusion=[
            make_supported_claim("CLAIM_002")
        ]
    )

    assert brief.document_type == "research_brief"
    assert len(brief.legal_analysis) == 1
    assert len(brief.conclusion) == 1


def test_duplicate_claim_ids_are_rejected():
    with pytest.raises(ValidationError):
        LegalBrief(
            title="Permit Revocation Brief",
            legal_issue="Whether notice is required.",
            legal_analysis=[
                make_supported_claim("CLAIM_001")
            ],
            conclusion=[
                make_supported_claim("CLAIM_001")
            ]
        )
