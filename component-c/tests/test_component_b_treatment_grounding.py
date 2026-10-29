
"""
Component C - Component B Metadata Integration Tests

Verifies that judicial-treatment references
work with Component B's actual PP1 structure.

No Gemini API calls are made.
No passage text is fabricated.
"""

from integration.component_b_adapter import (
    component_b_to_reasoning_request,
)

from reasoning.output_models import (
    AuthorityAnalysis,
    ReasoningResponse,
)

from brief.input_models import BriefGenerationRequest

from brief.output_models import (
    BriefClaim,
    BriefEvidenceReference,
    LegalBrief,
)

from brief.grounding_validator import (
    validate_brief_grounding,
)

from brief.evidence_audit import (
    create_evidence_audit,
)


def make_request():

    payload = {
        "query": "What can be determined from the supplied cases?",
        "case_facts": [
            "A legal dispute requires precedent analysis."
        ],
        "clusters": [
            {
                "seed_id": "case_001",
                "rrf_score": 0.0,
                "cases_cited": [
                    {
                        "target_id": "case_002",
                        "citation_type": "followed",
                        "evidence": "para 12",
                        "scope": "ratio"
                    }
                ],
                "cited_by": [
                    {
                        "target_id": "case_004",
                        "citation_type": "followed",
                        "evidence": "para 3",
                        "scope": None
                    }
                ],
                "legislation": [
                    {
                        "act_id": "leg_001",
                        "name": "Civil Procedure Code",
                        "section": "s.5"
                    }
                ],
                "appeal_chain": [
                    {
                        "related_id": "case_005",
                        "hops": 1
                    }
                ]
            },
            {
                "seed_id": "case_002",
                "rrf_score": 0.0,
                "cases_cited": [],
                "cited_by": [],
                "legislation": [],
                "appeal_chain": []
            }
        ]
    }

    source_request = component_b_to_reasoning_request(
        payload
    )

    reasoning = ReasoningResponse(
        legal_issue="Assessment of available case metadata.",
        authorities=[
            AuthorityAnalysis(
                case_id="case_001",
                relevance_to_issue="Retrieved by Component B.",
                judicial_treatment_summary=(
                    "Citation relationships are available."
                ),
                authority_assessment=(
                    "Legal holding cannot be determined "
                    "without judgment text."
                )
            ),
            AuthorityAnalysis(
                case_id="case_002",
                relevance_to_issue="Retrieved by Component B.",
                judicial_treatment_summary=(
                    "Referenced by case_001."
                ),
                authority_assessment=(
                    "Legal holding cannot be determined "
                    "without judgment text."
                )
            )
        ],
        cross_case_analysis=(
            "Available metadata identifies relationships "
            "but not complete legal holdings."
        ),
        application=(
            "Insufficient judgment text for a definitive "
            "application of legal principles."
        ),
        conclusion=(
            "A definitive legal conclusion cannot be "
            "established from this metadata alone."
        )
    )

    return BriefGenerationRequest(
        source_request=source_request,
        reasoning_result=reasoning,
        title="Metadata-Only Legal Research Brief"
    )


def make_brief(reference):

    return LegalBrief(
        title="Metadata-Only Legal Research Brief",
        legal_issue="Assessment of available metadata.",
        legal_analysis=[
            BriefClaim(
                claim_id="CLAIM_001",
                statement=(
                    "The supplied graph records a "
                    "judicial-treatment relationship."
                ),
                support_status="supported",
                evidence_references=[reference]
            )
        ],
        conclusion=[
            BriefClaim(
                claim_id="CLAIM_002",
                statement=(
                    "Insufficient source text is available "
                    "for a definitive legal conclusion."
                ),
                support_status="insufficient_evidence"
            )
        ]
    )


def test_component_b_has_no_passage_text():

    request = make_request()

    assert all(
        not precedent.passages
        for precedent in request.source_request.precedents
    )

    assert all(
        law.text is None
        for precedent in request.source_request.precedents
        for law in precedent.legislation
    )


def test_outgoing_treatment_is_grounded():

    request = make_request()

    reference = BriefEvidenceReference(
        source_type="judicial_treatment",
        source_case_id="case_001",
        target_case_id="case_002",
        treatment_status="followed",
        scope="ratio"
    )

    assert validate_brief_grounding(
        request,
        make_brief(reference)
    ) == []


def test_incoming_treatment_is_grounded():

    request = make_request()

    reference = BriefEvidenceReference(
        source_type="judicial_treatment",
        source_case_id="case_004",
        target_case_id="case_001",
        treatment_status="followed"
    )

    assert validate_brief_grounding(
        request,
        make_brief(reference)
    ) == []


def test_wrong_treatment_direction_is_rejected():

    request = make_request()

    reference = BriefEvidenceReference(
        source_type="judicial_treatment",
        source_case_id="case_002",
        target_case_id="case_001",
        treatment_status="followed"
    )

    errors = validate_brief_grounding(
        request,
        make_brief(reference)
    )

    assert errors


def test_audit_preserves_locator_without_inventing_text():

    request = make_request()

    reference = BriefEvidenceReference(
        source_type="judicial_treatment",
        source_case_id="case_001",
        target_case_id="case_002",
        treatment_status="followed",
        scope="ratio"
    )

    audit = create_evidence_audit(
        request,
        make_brief(reference)
    )

    citation = audit.claims[0].citations[0]

    assert citation.found
    assert citation.source_text is None
    assert "para 12" in citation.source_details
    assert audit.unresolved_references == 0
