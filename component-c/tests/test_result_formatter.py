
"""
Tests for Component C's readable reasoning formatter.

No Gemini API calls are made.
"""

from pathlib import Path

import pytest

from reasoning.output_models import ReasoningResponse
from reasoning.result_formatter import (
    format_reasoning_report,
)


FIXTURE_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "demo"
    / "day1_baseline_response.json"
)


@pytest.fixture
def day1_response():
    """Load the actual saved Day 1 demo fixture."""

    return ReasoningResponse.model_validate_json(
        FIXTURE_FILE.read_text(encoding="utf-8")
    )


def test_formatter_contains_all_main_sections(
    day1_response
):
    """All important reasoning sections must appear."""

    report = format_reasoning_report(day1_response)

    expected_sections = [
        "LEGAL ISSUE",
        "RELEVANT FACTS",
        "AUTHORITIES CONSIDERED",
        "AUTHORITY COMPARISON",
        "CROSS-CASE ANALYSIS",
        "LEGISLATION CONSIDERED",
        "APPLICATION TO FACTS",
        "CONCLUSION",
        "LIMITATIONS / INSUFFICIENT EVIDENCE",
    ]

    for section in expected_sections:
        assert section in report


def test_formatter_preserves_original_content(
    day1_response
):
    """The formatter must preserve generated analysis."""

    report = format_reasoning_report(day1_response)

    assert day1_response.legal_issue in report
    assert day1_response.cross_case_analysis in report
    assert day1_response.application in report
    assert day1_response.conclusion in report

    for authority in day1_response.authorities:
        assert authority.case_id in report
        assert authority.authority_assessment in report

    assert "MOCK_SC_001:P1" in report


def test_formatter_handles_missing_comparison(
    day1_response
):
    """Older Day 1 results must remain readable."""

    report = format_reasoning_report(day1_response)

    assert "Court Hierarchy:" in report

    assert "Not available in this response." in report

    assert "Chronology:" in report


def test_formatter_displays_day2_comparisons(
    day1_response
):
    """New structured comparison fields must be displayed."""

    data = day1_response.model_dump()

    data["authority_comparison"] = {
        "hierarchy_considerations": (
            "Supplied court levels were compared."
        ),
        "chronology_considerations": (
            "Judgment dates were compared."
        ),
        "judicial_treatment_considerations": (
            "Supplied treatment relationships were compared."
        ),
        "conflicts_or_distinctions": (
            "Relevant legal distinctions were identified."
        ),
    }

    response = ReasoningResponse.model_validate(data)

    report = format_reasoning_report(response)

    assert "Supplied court levels were compared." in report
    assert "Judgment dates were compared." in report
    assert (
        "Supplied treatment relationships were compared."
        in report
    )
    assert (
        "Relevant legal distinctions were identified."
        in report
    )


def test_formatter_does_not_modify_response(
    day1_response
):
    """Formatting must not change the underlying response."""

    original_data = day1_response.model_dump()

    format_reasoning_report(day1_response)

    assert day1_response.model_dump() == original_data
