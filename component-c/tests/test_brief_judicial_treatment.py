
"""
Tests for judicial-treatment evidence references.

Component C - Function 2

All test evidence is fictional.
No Gemini API requests are made.
"""

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from reasoning.input_models import (
    ReasoningRequest,
    Precedent,
    Passage,
    JudicialTreatment,
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
            "A permit was revoked without notice."
        ],
        reference_date=date(2026, 10, 12),
        precedents=[
            Precedent(
                case_id="MOCK_SC_001",
                passages=[
                    Passage(
                        passage_id="P1",
                        text="Prior notice is required."
                    )
                ],
                judicial_treatments=[
                    JudicialTreatment(
                        source_case_id="MOCK_SC_004",
                        target_case_id="MOCK_SC_001",
                        status="followed",
                        effective_date=date(2025, 1, 15),
                        scope=(
                            "prior notice for permit revocation"
                        )
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
                    "Followed by MOCK_SC_004."
                ),
                authority_assessment=(
                    "Supports prior notice."
                )
            )
        ],
        cross_case_analysis=(
            "The supplied authority supports notice."
        ),
        application="No notice was given.",
        conclusion="Prior notice is required."
    )

    return BriefGenerationRequest(
        source_request=source,
        reasoning_result=reasoning,
        title="Permit Revocation Research Brief"
    )


def make_reference(**changes):

    values = {
        "source_type": "judicial_treatment",
        "source_case_id": "MOCK_SC_004",
        "target_case_id": "MOCK_SC_001",
        "treatment_status": "followed",
        "effective_date": date(2025, 1, 15),
        "scope": "prior notice for permit revocation",
    }

    values.update(changes)

    return BriefEvidenceReference(**values)


def make_brief(reference):

    return LegalBrief(
        title="Permit Revocation Research Brief",
        legal_issue="Whether notice is required.",
        legal_analysis=[
            BriefClaim(
                claim_id="CLAIM_001",
                statement=(
                    "MOCK_SC_001 was followed by MOCK_SC_004."
                ),
                support_status="supported",
                evidence_references=[reference]
            )
        ],
        conclusion=[
            BriefClaim(
                claim_id="CLAIM_002",
                statement="Prior notice is ordinarily required.",
                support_status="insufficient_evidence"
            )
        ]
    )


def validate(reference):

    return validate_brief_grounding(
        make_request(),
        make_brief(reference)
    )


def test_valid_full_treatment_reference():

    assert validate(make_reference()) == []


def test_valid_minimal_treatment_reference():

    reference = make_reference(
        effective_date=None,
        scope=None
    )

    assert validate(reference) == []


def test_treatment_reference_requires_identifiers():

    with pytest.raises(ValidationError):

        BriefEvidenceReference(
            source_type="judicial_treatment",
            source_case_id="MOCK_SC_004"
        )


def test_wrong_source_case_is_rejected():

    errors = validate(
        make_reference(
            source_case_id="UNKNOWN_CASE"
        )
    )

    assert errors
    assert "Judicial-treatment reference" in errors[0]


def test_wrong_target_case_is_rejected():

    assert validate(
        make_reference(
            target_case_id="UNKNOWN_TARGET"
        )
    )


def test_wrong_treatment_status_is_rejected():

    assert validate(
        make_reference(
            treatment_status="overruled"
        )
    )


def test_wrong_effective_date_is_rejected():

    assert validate(
        make_reference(
            effective_date=date(2023, 1, 1)
        )
    )


def test_wrong_scope_is_rejected():

    assert validate(
        make_reference(
            scope="unrelated legal issue"
        )
    )


def test_treating_case_need_not_be_retrieved():

    request = make_request()

    retrieved_ids = {
        precedent.case_id
        for precedent in request.source_request.precedents
    }

    assert "MOCK_SC_004" not in retrieved_ids

    assert validate_brief_grounding(
        request,
        make_brief(make_reference())
    ) == []


def test_treatment_section_is_validated():

    brief = make_brief(make_reference())

    brief.precedent_treatment.append(
        BriefClaim(
            claim_id="CLAIM_003",
            statement="Incorrect treatment statement.",
            support_status="supported",
            evidence_references=[
                make_reference(
                    treatment_status="overruled"
                )
            ]
        )
    )

    errors = validate_brief_grounding(
        make_request(),
        brief
    )

    assert errors
    assert "precedent_treatment/CLAIM_003" in errors[0]


class FakeProvider:

    def __init__(self, brief):
        self.brief = brief

    def generate(self, system_prompt, user_prompt):
        return self.brief.model_dump_json()


def test_service_accepts_valid_treatment_reference():

    result = run_legal_brief_generation(
        make_request(),
        FakeProvider(
            make_brief(make_reference())
        )
    )

    assert isinstance(result, LegalBrief)


def test_service_rejects_invalid_treatment_reference():

    with pytest.raises(
        ValueError,
        match="Brief grounding validation failed"
    ):

        run_legal_brief_generation(
            make_request(),
            FakeProvider(
                make_brief(
                    make_reference(
                        treatment_status="overruled"
                    )
                )
            )
        )


def test_existing_recorded_brief_still_parses():
    """
    The original recorded Gemini output should
    remain compatible with the extended models.
    """

    project_root = Path(__file__).resolve().parents[1]

    file_path = (
        project_root
        / "data"
        / "demo"
        / "briefs"
        / "baseline_legal_brief.json"
    )

    brief = LegalBrief.model_validate_json(
        file_path.read_text(encoding="utf-8")
    )

    assert brief.document_type == "research_brief"
    assert brief.title
    assert brief.legal_analysis
