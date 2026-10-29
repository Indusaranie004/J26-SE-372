
"""
Component C - Function 2
Evidence Audit Tests

Tests claim-to-source evidence resolution
using recorded fictional development results.

No Gemini calls are made.
"""

from pathlib import Path

from brief.input_models import BriefGenerationRequest
from brief.output_models import (
    BriefClaim,
    BriefEvidenceReference,
    LegalBrief,
)

from brief.evidence_audit import (
    create_evidence_audit,
    format_evidence_audit,
)

from scripts.run_brief_experiment import (
    prepare_brief_request,
)

from scripts.run_insufficient_evidence_brief import (
    prepare_request as prepare_insufficient_request,
)


BASE_DIR = Path(__file__).resolve().parents[1]


def load_baseline():

    request = prepare_brief_request()

    path = (
        BASE_DIR
        / "data"
        / "demo"
        / "briefs"
        / "baseline_legal_brief.json"
    )

    brief = LegalBrief.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    return request, brief


def load_insufficient():

    request = prepare_insufficient_request()

    path = (
        BASE_DIR
        / "data"
        / "demo"
        / "briefs"
        / "insufficient_evidence_legal_brief.json"
    )

    brief = LegalBrief.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    return request, brief


def make_minimal_brief(
    request: BriefGenerationRequest,
    reference: BriefEvidenceReference,
):

    return LegalBrief(
        title=request.title,
        legal_issue="Fictional permit revocation.",
        legal_analysis=[
            BriefClaim(
                claim_id="CLAIM_A",
                statement="Test legal proposition.",
                support_status="supported",
                evidence_references=[reference],
            )
        ],
        conclusion=[
            BriefClaim(
                claim_id="CLAIM_B",
                statement="Further review is necessary.",
                support_status="insufficient_evidence",
            )
        ],
    )


def test_baseline_audit_contains_all_claims():

    request, brief = load_baseline()

    audit = create_evidence_audit(
        request,
        brief,
    )

    assert audit.total_claims == 23

    assert audit.total_references == 39

    assert audit.unresolved_references == 0


def test_audit_displays_exact_original_case_fact():

    request, brief = load_baseline()

    audit = create_evidence_audit(
        request,
        brief,
    )

    first_claim = audit.claims[0]

    assert first_claim.claim_id == "CLAIM_001"

    assert first_claim.citations[0].source_text == (
        request.source_request.case_facts[0]
    )


def test_original_treatment_citations_are_flagged():

    request, brief = load_baseline()

    audit = create_evidence_audit(
        request,
        brief,
    )

    treatment_claims = [
        claim
        for claim in audit.claims
        if claim.section == "precedent_treatment"
    ]

    assert len(treatment_claims) == 3

    assert all(
        claim.review_flags
        for claim in treatment_claims
    )


def test_missing_passage_is_detected():

    request, _ = load_baseline()

    reference = BriefEvidenceReference(
        source_type="case_passage",
        case_id="MOCK_SC_001",
        passage_id="NONEXISTENT_PASSAGE",
    )

    brief = make_minimal_brief(
        request,
        reference,
    )

    audit = create_evidence_audit(
        request,
        brief,
    )

    assert audit.unresolved_references == 1

    assert audit.flagged_claims >= 1


def test_valid_judicial_treatment_is_resolved():

    request, _ = load_baseline()

    treatment = next(
        treatment
        for precedent in request.source_request.precedents
        for treatment in precedent.judicial_treatments
    )

    reference = BriefEvidenceReference(
        source_type="judicial_treatment",
        source_case_id=treatment.source_case_id,
        target_case_id=treatment.target_case_id,
        treatment_status=treatment.status,
        effective_date=treatment.effective_date,
        scope=treatment.scope,
    )

    brief = make_minimal_brief(
        request,
        reference,
    )

    audit = create_evidence_audit(
        request,
        brief,
    )

    assert audit.unresolved_references == 0

    assert audit.claims[0].citations[0].found


def test_audit_markdown_contains_evidence():

    request, brief = load_baseline()

    audit = create_evidence_audit(
        request,
        brief,
    )

    markdown = format_evidence_audit(
        audit
    )

    assert "# Evidence Audit:" in markdown

    assert "CLAIM_001" in markdown

    assert request.source_request.case_facts[0] in markdown

    assert "Human assessment: unverified" not in markdown

    assert "**Human assessment:** Not yet evaluated" in markdown

    assert "does NOT establish semantic" in markdown


def test_insufficient_evidence_status_is_preserved():

    request, brief = load_insufficient()

    audit = create_evidence_audit(
        request,
        brief,
    )

    conclusion_claims = [
        claim
        for claim in audit.claims
        if claim.section == "conclusion"
    ]

    assert any(
        claim.model_support_status
        == "insufficient_evidence"
        for claim in conclusion_claims
    )


def test_audit_generation_does_not_modify_brief():

    request, brief = load_baseline()

    before = brief.model_dump_json()

    audit = create_evidence_audit(
        request,
        brief,
    )

    format_evidence_audit(audit)

    assert brief.model_dump_json() == before


def test_audit_output_is_deterministic():

    request, brief = load_baseline()

    first = format_evidence_audit(
        create_evidence_audit(request, brief)
    )

    second = format_evidence_audit(
        create_evidence_audit(request, brief)
    )

    assert first == second
