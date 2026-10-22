
"""
Tests for Day 2 controlled reasoning scenarios.

Verifies that scenarios are valid, independent,
and contain only the intended experimental changes.

No Gemini API calls are made.
"""

from copy import deepcopy

import pytest

from reasoning.input_models import ReasoningRequest
from scripts.prepare_day2_scenarios import (
    create_scenarios,
    load_original_request,
)


@pytest.fixture
def scenarios():
    """Generate all four test scenarios in memory."""
    return create_scenarios()


def test_all_scenarios_generated(scenarios):
    """All expected experiment scenarios must exist."""

    expected_names = {
        "scenario_1_baseline",
        "scenario_2_treatment_changed",
        "scenario_3_hierarchy_changed",
        "scenario_4_insufficient_evidence",
    }

    assert set(scenarios.keys()) == expected_names

    for scenario in scenarios.values():
        assert isinstance(scenario, ReasoningRequest)
        assert len(scenario.precedents) == 3


def test_baseline_matches_original(scenarios):
    """The baseline must be identical to our original input."""

    original = load_original_request()

    baseline = scenarios["scenario_1_baseline"]

    assert baseline.model_dump() == original.model_dump()


def test_treatment_mutation(scenarios):
    """Only intended treatment and validity metadata changes."""

    original = load_original_request()

    variant = scenarios["scenario_2_treatment_changed"]

    original_case = next(
        p for p in original.precedents
        if p.case_id == "MOCK_SC_003"
    )

    modified_case = next(
        p for p in variant.precedents
        if p.case_id == "MOCK_SC_003"
    )

    # Judicial treatment changed
    assert (
        original_case.judicial_treatments[0].status
        == "overruled"
    )

    assert (
        modified_case.judicial_treatments[0].status
        == "followed"
    )

    # Validity metadata changed consistently
    assert modified_case.validity.status == "good_law"

    assert modified_case.validity.safe_to_cite is True

    # Core legal evidence must remain unchanged
    assert modified_case.passages == original_case.passages
    assert modified_case.legislation == original_case.legislation
    assert modified_case.court == original_case.court
    assert modified_case.judgment_date == original_case.judgment_date

    # Other authorities must remain identical
    assert (
        variant.precedents[:2]
        == original.precedents[:2]
    )

    assert variant.query == original.query
    assert variant.case_facts == original.case_facts


def test_hierarchy_mutation(scenarios):
    """Only the intended court metadata should change."""

    original = load_original_request()

    variant = scenarios["scenario_3_hierarchy_changed"]

    original_data = original.model_dump()
    modified_data = variant.model_dump()

    # Construct exactly what the changed scenario should contain
    expected_data = deepcopy(original_data)

    expected_case = next(
        p for p in expected_data["precedents"]
        if p["case_id"] == "MOCK_CA_002"
    )

    expected_case["court"] = "Supreme Court"
    expected_case["case_number"] = "MOCK/SC/002/2018"

    # Full comparison detects unexpected metadata changes
    assert modified_data == expected_data


def test_insufficient_evidence_mutation(scenarios):
    """Only the legal question should change."""

    original = load_original_request()

    variant = scenarios["scenario_4_insufficient_evidence"]

    assert (
        "financial compensation"
        in variant.query
    )

    assert variant.query != original.query

    # Existing evidence and facts must remain identical
    assert variant.case_facts == original.case_facts

    assert variant.precedents == original.precedents

    assert variant.reference_date == original.reference_date

    # Confirm the generated input remains valid JSON
    restored = ReasoningRequest.model_validate_json(
        variant.model_dump_json()
    )

    assert restored == variant
