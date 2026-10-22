
"""
Tests for the structured legal Context Builder.

Verifies precedent metadata, judicial-treatment direction,
temporal applicability, and missing information handling.
"""

from datetime import date
from pathlib import Path

import pytest

from reasoning.input_models import ReasoningRequest
from reasoning.context_builder import build_reasoning_context


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "reasoning"
    / "data"
    / "mock_case_data.json"
)


@pytest.fixture
def reasoning_request():
    """Load the fictional precedent dataset."""

    return ReasoningRequest.model_validate_json(
        DATA_FILE.read_text(encoding="utf-8")
    )


def test_precedent_overview(reasoning_request):
    """All supplied authorities must appear in the context."""

    context = build_reasoning_context(reasoning_request)

    assert "PRECEDENT OVERVIEW" in context
    assert "Total precedents supplied: 3" in context

    assert "MOCK_SC_001" in context
    assert "MOCK_CA_002" in context
    assert "MOCK_SC_003" in context

    assert "Court: Supreme Court" in context
    assert "Court: Court of Appeal" in context

    assert "Passage ID: P1" in context
    assert "Mock Fair Administrative Procedure Act" in context


def test_judicial_treatment_direction(reasoning_request):
    """Incoming and outgoing relationships must be identified."""

    context = build_reasoning_context(reasoning_request)

    assert (
        "MOCK_SC_004 --followed--> MOCK_SC_001"
        in context
    )

    assert (
        "Direction: INCOMING - another case treats this precedent."
        in context
    )

    # Create a separate scenario with an outgoing relationship
    modified = reasoning_request.model_copy(deep=True)

    treatment = modified.precedents[0].judicial_treatments[0]

    treatment.source_case_id = "MOCK_SC_001"
    treatment.target_case_id = "MOCK_SC_009"

    modified_context = build_reasoning_context(modified)

    assert (
        "MOCK_SC_001 --followed--> MOCK_SC_009"
        in modified_context
    )

    assert (
        "Direction: OUTGOING - this precedent treats another case."
        in modified_context
    )


def test_future_judicial_treatment(reasoning_request):
    """Future treatment must be flagged against the reference date."""

    modified = reasoning_request.model_copy(deep=True)

    treatment = modified.precedents[0].judicial_treatments[0]

    treatment.effective_date = date(2027, 1, 1)

    context = build_reasoning_context(modified)

    assert "Effective Date: 2027-01-01" in context

    assert (
        "AFTER REFERENCE DATE"
        in context
    )

    assert (
        "must not be treated as effective"
        in context
    )


def test_missing_reference_date(reasoning_request):
    """Temporal applicability must not be invented."""

    modified = reasoning_request.model_copy(deep=True)

    modified.reference_date = None

    context = build_reasoning_context(modified)

    assert (
        "Cannot assess: reference date not supplied."
        in context
    )


def test_missing_legal_metadata(reasoning_request):
    """Missing evidence must be represented explicitly."""

    modified = reasoning_request.model_copy(deep=True)

    modified.case_facts = []

    precedent = modified.precedents[0]

    precedent.validity = None
    precedent.passages = []
    precedent.legislation = []
    precedent.judicial_treatments = []
    precedent.litigation_history = []

    context = build_reasoning_context(modified)

    assert "No case facts supplied." in context

    assert (
        "Validity information not supplied."
        in context
    )

    assert (
        "No relevant passages supplied."
        in context
    )

    assert (
        "No legislation supplied."
        in context
    )

    assert (
        "No judicial treatment information supplied."
        in context
    )

    assert (
        "No litigation history supplied."
        in context
    )
