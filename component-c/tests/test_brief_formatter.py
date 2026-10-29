
"""
Tests for Function 2 Legal Brief Formatter.

Uses the actual recorded fictional brief
and additional synthetic reference examples.

No Gemini API calls are made.
"""

from datetime import date
from pathlib import Path

import pytest

from brief.output_models import (
    BriefClaim,
    BriefEvidenceReference,
    LegalBrief,
)

from brief.brief_formatter import (
    BRIEF_SECTIONS,
    format_evidence_reference,
    format_legal_brief,
)


@pytest.fixture
def recorded_brief():

    project_root = Path(__file__).resolve().parents[1]

    file_path = (
        project_root
        / "data"
        / "demo"
        / "briefs"
        / "baseline_legal_brief.json"
    )

    return LegalBrief.model_validate_json(
        file_path.read_text(encoding="utf-8")
    )


def make_minimal_brief():

    return LegalBrief(
        title="Example Legal Brief",
        legal_issue="Whether notice is required.",
        legal_analysis=[
            BriefClaim(
                claim_id="CLAIM_001",
                statement=(
                    "The supplied evidence is insufficient."
                ),
                support_status="insufficient_evidence",
            )
        ],
        conclusion=[
            BriefClaim(
                claim_id="CLAIM_002",
                statement="No conclusion can be established.",
                support_status="insufficient_evidence",
            )
        ],
    )


def test_recorded_brief_formats_successfully(
    recorded_brief
):

    report = format_legal_brief(recorded_brief)

    assert report.startswith(
        "# Business Permit Revocation"
    )

    assert "## Legal Issue" in report

    assert "## 10. Limitations" in report

    assert "CLAIM_023" in report


def test_all_brief_sections_are_included(
    recorded_brief
):

    report = format_legal_brief(recorded_brief)

    for number, (heading, _) in enumerate(
        BRIEF_SECTIONS,
        start=1
    ):

        assert (
            f"## {number}. {heading}"
            in report
        )


def test_original_claim_statements_are_preserved(
    recorded_brief
):

    report = format_legal_brief(recorded_brief)

    for _, attribute in BRIEF_SECTIONS:

        for claim in getattr(
            recorded_brief,
            attribute
        ):

            assert claim.claim_id in report
            assert claim.statement in report


def test_case_and_legislation_references_are_shown(
    recorded_brief
):

    report = format_legal_brief(recorded_brief)

    assert "Case MOCK_SC_001, passage P1" in report

    assert "MOCK_ACT_001" in report

    assert "Section 10" in report


def test_fact_indices_are_displayed_from_one(
    recorded_brief
):

    report = format_legal_brief(recorded_brief)

    assert "**Evidence:** Fact 1" in report

    assert "**Evidence:** Fact 5" in report


def test_judicial_treatment_displays_direction_and_scope():

    reference = BriefEvidenceReference(
        source_type="judicial_treatment",
        source_case_id="MOCK_SC_004",
        target_case_id="MOCK_SC_001",
        treatment_status="followed",
        effective_date=date(2025, 1, 15),
        scope="prior notice for permit revocation",
    )

    text = format_evidence_reference(reference)

    assert (
        "MOCK_SC_004 --followed--> MOCK_SC_001"
        in text
    )

    assert "2025-01-15" in text

    assert (
        "prior notice for permit revocation"
        in text
    )


def test_missing_evidence_is_explicit():

    brief = make_minimal_brief()

    report = format_legal_brief(brief)

    assert (
        "No source reference cited."
        in report
    )

    assert (
        "insufficient evidence"
        in report
    )


def test_empty_sections_are_not_silently_omitted():

    brief = make_minimal_brief()

    report = format_legal_brief(brief)

    assert "## 1. Relevant Facts" in report

    assert (
        "No claims recorded in this section."
        in report
    )


def test_formatter_does_not_modify_the_brief(
    recorded_brief
):

    original = recorded_brief.model_dump_json()

    format_legal_brief(recorded_brief)

    assert (
        recorded_brief.model_dump_json()
        == original
    )
