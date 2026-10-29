
"""
Tests for the Day 2 experiment runner.

Tests:
1. Dry-run execution
2. Individual scenario selection
3. Result saving and overwrite protection
4. Handling failed experiments

All tests run without Gemini API requests.
"""

import sys

import pytest

from reasoning.output_models import ReasoningResponse
from reasoning import reasoning_service

from scripts import run_day2_experiments as runner
from scripts.prepare_day2_scenarios import create_scenarios


@pytest.fixture
def prepared_scenarios(tmp_path, monkeypatch):
    """
    Create temporary scenario files for testing.

    Tests do not depend on previously generated
    files inside the outputs directory.
    """

    scenario_dir = tmp_path / "scenarios"
    result_dir = tmp_path / "results"

    scenario_dir.mkdir()

    for name, request in create_scenarios().items():

        file_path = scenario_dir / f"{name}.json"

        file_path.write_text(
            request.model_dump_json(indent=2),
            encoding="utf-8"
        )

    monkeypatch.setattr(
        runner,
        "SCENARIO_DIR",
        scenario_dir
    )

    monkeypatch.setattr(
        runner,
        "RESULT_DIR",
        result_dir
    )

    return tmp_path


def test_dry_run_all_scenarios(
    prepared_scenarios,
    monkeypatch,
    capsys
):
    """Default execution must inspect all scenarios."""

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_day2_experiments"]
    )

    runner.main()

    output = capsys.readouterr().out

    assert "DRY RUN COMPLETED" in output

    for name in runner.SCENARIO_NAMES:
        assert name.upper() in output

    assert "No Gemini API requests were made." in output

    assert not runner.RESULT_DIR.exists()


def test_single_scenario_selection(
    prepared_scenarios,
    monkeypatch,
    capsys
):
    """The runner should inspect only the selected scenario."""

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_day2_experiments",
            "--scenario",
            "scenario_3_hierarchy_changed"
        ]
    )

    runner.main()

    output = capsys.readouterr().out

    assert "SCENARIO_3_HIERARCHY_CHANGED" in output

    assert "SCENARIO_1_BASELINE" not in output

    assert "DRY RUN COMPLETED" in output


def make_fake_reasoning_response(request):
    """
    Create a controlled response for runner testing.

    This is not a genuine LLM-generated analysis.
    """

    return ReasoningResponse.model_validate({
        "legal_issue": request.query,
        "authorities": [
            {
                "case_id": "MOCK_SC_001",
                "relevance_to_issue": "Test relevance.",
                "validity_status": "good_law",
                "judicial_treatment_summary": "Test treatment.",
                "authority_assessment": "Test assessment."
            }
        ],
        "authority_comparison": {
            "hierarchy_considerations": "Test hierarchy.",
            "chronology_considerations": "Test chronology.",
            "judicial_treatment_considerations": "Test treatment.",
            "conflicts_or_distinctions": "Test conflicts."
        },
        "cross_case_analysis": "Test synthesis.",
        "application": "Test application.",
        "conclusion": "Test conclusion."
    })


def test_live_result_saving_and_skip(
    prepared_scenarios,
    monkeypatch
):
    """
    Simulate successful live execution without an API.

    Verify saving and overwrite protection.
    """

    calls = []

    def fake_reasoning(request, provider):
        calls.append(request)
        return make_fake_reasoning_response(request)

    monkeypatch.setattr(
        reasoning_service,
        "run_cross_case_reasoning",
        fake_reasoning
    )

    name = "scenario_1_baseline"

    request = runner.load_scenario(name)

    fake_provider = object()

    # First execution should save the response
    runner.run_live_experiment(
        name,
        request,
        fake_provider
    )

    output_file = (
        runner.RESULT_DIR / f"{name}_response.json"
    )

    assert output_file.exists()
    assert len(calls) == 1

    saved = ReasoningResponse.model_validate_json(
        output_file.read_text(encoding="utf-8")
    )

    assert saved.conclusion == "Test conclusion."

    assert (
        saved.authority_comparison.hierarchy_considerations
        == "Test hierarchy."
    )

    # Second execution should skip the existing file
    runner.run_live_experiment(
        name,
        request,
        fake_provider
    )

    assert len(calls) == 1


def test_failed_experiment_does_not_save(
    prepared_scenarios,
    monkeypatch
):
    """
    Failed model generation must not create
    an accepted reasoning response file.
    """

    def failing_reasoning(request, provider):
        raise RuntimeError("Simulated API failure")

    monkeypatch.setattr(
        reasoning_service,
        "run_cross_case_reasoning",
        failing_reasoning
    )

    name = "scenario_1_baseline"

    request = runner.load_scenario(name)

    with pytest.raises(
        RuntimeError,
        match="Simulated API failure"
    ):
        runner.run_live_experiment(
            name,
            request,
            object()
        )

    output_file = (
        runner.RESULT_DIR / f"{name}_response.json"
    )

    assert not output_file.exists()
