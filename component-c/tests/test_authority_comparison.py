
"""
Tests for structured authority comparison.

Verifies backward compatibility with Day 1 outputs
and validates the new comparison fields.

No Gemini API requests are made.
"""

import json

import pytest
from pydantic import ValidationError

from reasoning.output_models import (
    AuthorityComparison,
    ReasoningResponse,
)


def make_valid_response():
    """Build a minimal valid reasoning response."""

    return {
        "legal_issue": "Is prior notice required?",
        "relevant_facts": [
            "The permit was revoked without notice."
        ],
        "authorities": [
            {
                "case_id": "MOCK_SC_001",
                "relevance_to_issue": (
                    "Addresses procedural fairness."
                ),
                "validity_status": "good_law",
                "judicial_treatment_summary": (
                    "Followed by a later decision."
                ),
                "authority_assessment": (
                    "Supports the notice requirement."
                ),
                "supporting_evidence": [
                    {
                        "case_id": "MOCK_SC_001",
                        "passage_id": "P1"
                    }
                ]
            }
        ],
        "cross_case_analysis": (
            "The supplied authority supports notice."
        ),
        "legislation_considered": [],
        "application": (
            "No prior notice was given."
        ),
        "conclusion": (
            "Prior notice appears required."
        ),
        "limitations_or_insufficient_evidence": []
    }


def test_backward_compatibility():
    """
    Day 1 responses without authority_comparison
    must still be accepted.
    """

    old_response = make_valid_response()

    result = ReasoningResponse.model_validate_json(
        json.dumps(old_response)
    )

    assert isinstance(
        result.authority_comparison,
        AuthorityComparison
    )

    assert (
        result.authority_comparison.hierarchy_considerations
        is None
    )

    assert (
        result.authority_comparison.chronology_considerations
        is None
    )


def test_complete_authority_comparison():
    """All four comparative considerations can be saved."""

    response_data = make_valid_response()

    response_data["authority_comparison"] = {
        "hierarchy_considerations": (
            "Supreme Court and Court of Appeal levels "
            "were compared."
        ),
        "chronology_considerations": (
            "The relevant judgment dates were considered."
        ),
        "judicial_treatment_considerations": (
            "The followed and overruled relationships "
            "were evaluated."
        ),
        "conflicts_or_distinctions": (
            "The emergency exception was distinguished "
            "from an ordinary permit revocation."
        )
    }

    result = ReasoningResponse.model_validate(
        response_data
    )

    comparison = result.authority_comparison

    assert "Supreme Court" in (
        comparison.hierarchy_considerations
    )

    assert "judgment dates" in (
        comparison.chronology_considerations
    )

    assert "overruled" in (
        comparison.judicial_treatment_considerations
    )

    assert "emergency exception" in (
        comparison.conflicts_or_distinctions
    )


def test_partial_authority_comparison():
    """
    Missing considerations should remain None,
    not become fabricated text.
    """

    comparison = AuthorityComparison(
        hierarchy_considerations=(
            "Only one court level was supplied."
        )
    )

    assert comparison.hierarchy_considerations is not None

    assert comparison.chronology_considerations is None

    assert comparison.judicial_treatment_considerations is None

    assert comparison.conflicts_or_distinctions is None


def test_empty_comparison_text_rejected():
    """An explicitly empty consideration is invalid."""

    with pytest.raises(ValidationError):
        AuthorityComparison(
            hierarchy_considerations=""
        )


def test_unexpected_comparison_field_rejected():
    """Unexpected output fields must not be accepted."""

    with pytest.raises(ValidationError):
        AuthorityComparison.model_validate({
            "hierarchy_considerations": (
                "Court hierarchy considered."
            ),
            "invented_authority_rank": "highest"
        })
