
"""
Tests for Component C Function 2 grounding.

No Gemini API requests are made.
"""

import pytest

from reasoning.input_models import (
    ReasoningRequest,
    Precedent,
    Passage,
    Legislation,
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

from brief.grounding_validator import validate_brief_grounding

from brief.brief_service import run_legal_brief_generation


def make_request():

    source = ReasoningRequest(
        query="Is prior notice required?",
        case_facts=[
            "The business had a valid permit.",
            "The permit was revoked without notice.",
        ],
        precedents=[
            Precedent(
                case_id="MOCK_SC_001",
                passages=[
                    Passage(
                        passage_id="P1",
                        text="Reasonable notice is required."
                    )
                ],
                legislation=[
                    Legislation(
                        act_id="MOCK_ACT_001",
                        name="Mock Procedure Act",
                        section="Section 10",
                        text="A hearing must be provided."
                    )
                ]
            ),
            Precedent(
                case_id="MOCK_CA_002",
                passages=[
                    Passage(
                        passage_id="P2",
                        text="Emergency action may be permitted."
                    )
                ]
            ),
        ]
    )

    reasoning = ReasoningResponse(
        legal_issue="Whether notice is required.",
        authorities=[
            AuthorityAnalysis(
                case_id="MOCK_SC_001",
                relevance_to_issue="Directly relevant.",
                judicial_treatment_summary="Not supplied.",
                authority_assessment="Supports notice."
            ),
            AuthorityAnalysis(
                case_id="MOCK_CA_002",
                relevance_to_issue="Emergency exception.",
                judicial_treatment_summary="Not supplied.",
                authority_assessment="Limited relevance."
            )
        ],
        cross_case_analysis="Notice is ordinarily required.",
        application="No notice was provided.",
        conclusion="Notice is required."
    )

    return BriefGenerationRequest(
        source_request=source,
        reasoning_result=reasoning,
        title="Permit Revocation Research Brief"
    )


def make_brief(reference=None, status="supported"):

    references = (
        [reference]
        if reference is not None
        else []
    )

    claim = BriefClaim(
        claim_id="CLAIM_001",
        statement="Prior notice is required.",
        support_status=status,
        evidence_references=references
    )

    conclusion = BriefClaim(
        claim_id="CLAIM_002",
        statement="Evidence must be assessed.",
        support_status="insufficient_evidence"
    )

    return LegalBrief(
        title="Permit Revocation Research Brief",
        legal_issue="Is prior notice required?",
        legal_analysis=[claim],
        conclusion=[conclusion]
    )


def check(reference):
    return validate_brief_grounding(
        make_request(),
        make_brief(reference)
    )


def test_valid_case_passage():
    reference = BriefEvidenceReference(
        source_type="case_passage",
        case_id="MOCK_SC_001",
        passage_id="P1"
    )

    assert check(reference) == []


def test_valid_case_fact():
    reference = BriefEvidenceReference(
        source_type="case_fact",
        fact_index=1
    )

    assert check(reference) == []


def test_valid_legislation():
    reference = BriefEvidenceReference(
        source_type="legislation",
        act_id="MOCK_ACT_001",
        legislation_name="Mock Procedure Act",
        section="Section 10"
    )

    assert check(reference) == []


def test_unknown_case_is_rejected():
    reference = BriefEvidenceReference(
        source_type="case_passage",
        case_id="MADE_UP_CASE",
        passage_id="P1"
    )

    assert any(
        "Unknown case ID" in error
        for error in check(reference)
    )


def test_unknown_passage_is_rejected():
    reference = BriefEvidenceReference(
        source_type="case_passage",
        case_id="MOCK_SC_001",
        passage_id="P999"
    )

    assert any(
        "Passage ID" in error
        for error in check(reference)
    )


def test_passage_from_another_case_is_rejected():
    reference = BriefEvidenceReference(
        source_type="case_passage",
        case_id="MOCK_SC_001",
        passage_id="P2"
    )

    assert check(reference)


def test_invalid_fact_index_is_rejected():
    reference = BriefEvidenceReference(
        source_type="case_fact",
        fact_index=99
    )

    assert any(
        "Invalid fact index" in error
        for error in check(reference)
    )


def test_unknown_legislation_is_rejected():
    reference = BriefEvidenceReference(
        source_type="legislation",
        act_id="UNKNOWN_ACT"
    )

    assert check(reference)


def test_wrong_legislation_section_is_rejected():
    reference = BriefEvidenceReference(
        source_type="legislation",
        act_id="MOCK_ACT_001",
        section="Section 99"
    )

    assert check(reference)


def test_legislation_identifiers_must_match_same_record():
    reference = BriefEvidenceReference(
        source_type="legislation",
        act_id="MOCK_ACT_001",
        legislation_name="Different Act"
    )

    assert check(reference)


def test_insufficient_evidence_without_reference_is_allowed():
    brief = make_brief(
        reference=None,
        status="insufficient_evidence"
    )

    assert validate_brief_grounding(
        make_request(),
        brief
    ) == []


def test_validation_checks_counterarguments():
    brief = make_brief(
        BriefEvidenceReference(
            source_type="case_passage",
            case_id="MOCK_SC_001",
            passage_id="P1"
        )
    )

    brief.counterarguments.append(
        BriefClaim(
            claim_id="CLAIM_003",
            statement="An unsupported counterargument.",
            support_status="supported",
            evidence_references=[
                BriefEvidenceReference(
                    source_type="case_passage",
                    case_id="MOCK_SC_001",
                    passage_id="P999"
                )
            ]
        )
    )

    assert validate_brief_grounding(
        make_request(),
        brief
    )


class FakeProvider:
    def __init__(self, brief):
        self.brief = brief

    def generate(self, system_prompt, user_prompt):
        return self.brief.model_dump_json()


def test_service_accepts_grounded_brief():
    brief = make_brief(
        BriefEvidenceReference(
            source_type="case_passage",
            case_id="MOCK_SC_001",
            passage_id="P1"
        )
    )

    result = run_legal_brief_generation(
        make_request(),
        FakeProvider(brief)
    )

    assert result.title == "Permit Revocation Research Brief"


def test_service_rejects_invalid_reference():
    brief = make_brief(
        BriefEvidenceReference(
            source_type="case_passage",
            case_id="MOCK_SC_001",
            passage_id="P999"
        )
    )

    with pytest.raises(
        ValueError,
        match="Brief grounding validation failed"
    ):
        run_legal_brief_generation(
            make_request(),
            FakeProvider(brief)
        )
