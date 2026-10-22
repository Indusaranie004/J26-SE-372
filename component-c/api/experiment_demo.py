
"""
Component C - Recorded Experiment Demonstration API

Provides access to the four previously generated
Gemini reasoning experiments.

- No new Gemini requests
- No new legal reasoning
- Uses version-controlled experiment files
- Validates each loaded response
- Provides a focused baseline comparison
"""

import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.recorded_demo import RecordedDemoResponse
from reasoning.output_models import ReasoningResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/reasoning/demo",
    tags=["Recorded Experiments"]
)

BASE_DIR = Path(__file__).resolve().parents[1]

EXPERIMENT_DIR = (
    BASE_DIR / "data" / "demo" / "live_experiments"
)

SCENARIOS = {
    "scenario_1_baseline":
        "Original precedent hierarchy and treatment",

    "scenario_2_treatment_changed":
        "Changed judicial treatment and validity",

    "scenario_3_hierarchy_changed":
        "Changed court hierarchy metadata",

    "scenario_4_insufficient_evidence":
        "Question with insufficient legal evidence",
}


class ExperimentListItem(BaseModel):
    scenario: str
    description: str
    available: bool


class ComparisonSide(BaseModel):
    validity_status: str
    judicial_treatment_summary: str
    authority_assessment: str
    conflicts_or_distinctions: str
    conclusion: str


class ExperimentComparisonResponse(BaseModel):
    mode: Literal["recorded"]
    comparison_type: str
    compared_case_id: str
    changed_input_metadata: list[str]
    baseline_scenario: str
    modified_scenario: str
    baseline: ComparisonSide
    modified: ComparisonSide
    note: str


def _load_experiment(scenario: str) -> RecordedDemoResponse:
    """
    Load a known, saved experiment.

    Only allow scenario names from SCENARIOS.
    This prevents arbitrary file-path access.
    """

    if scenario not in SCENARIOS:
        raise HTTPException(
            status_code=404,
            detail="Unknown experiment scenario."
        )

    file_path = EXPERIMENT_DIR / f"{scenario}_response.json"

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="The recorded experiment file was not found."
        )

    try:
        saved_json = file_path.read_text(encoding="utf-8")

        result = ReasoningResponse.model_validate_json(
            saved_json
        )

    except (OSError, ValueError) as exc:
        logger.warning(
            "Could not load experiment %s: %s",
            scenario,
            exc
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The experiment file could not "
                "be read or validated."
            )
        ) from exc

    comparison = result.authority_comparison

    fields = [
        comparison.hierarchy_considerations,
        comparison.chronology_considerations,
        comparison.judicial_treatment_considerations,
        comparison.conflicts_or_distinctions,
    ]

    comparison_available = all(
        isinstance(value, str) and bool(value.strip())
        for value in fields
    )

    return RecordedDemoResponse(
        mode="recorded",
        scenario=scenario,
        note=(
            "Previously saved Gemini experiment. "
            "No live model request was made. "
            "Uses fictional legal evidence. "
            "Structural validation does not establish "
            "legal correctness."
        ),
        comparison_available=comparison_available,
        result=result
    )


@router.get(
    "/experiments",
    response_model=list[ExperimentListItem],
    summary="List recorded reasoning experiments"
)
def list_recorded_experiments():
    """
    List all four prepared experiments and
    indicate whether their JSON files exist.
    """

    return [
        ExperimentListItem(
            scenario=scenario,
            description=description,
            available=(
                EXPERIMENT_DIR
                / f"{scenario}_response.json"
            ).is_file()
        )
        for scenario, description in SCENARIOS.items()
    ]


@router.get(
    "/experiments/{scenario}",
    response_model=RecordedDemoResponse,
    summary="View a recorded reasoning experiment"
)
def get_recorded_experiment(
    scenario: str
) -> RecordedDemoResponse:
    """
    Return the complete saved response
    for one supported scenario.
    """

    return _load_experiment(scenario)


def _comparison_side(
    result: ReasoningResponse,
    case_id: str
) -> ComparisonSide:
    """
    Extract existing model-generated content
    for a specific precedent.

    This function does not interpret or
    generate additional legal reasoning.
    """

    authority = next(
        (
            item
            for item in result.authorities
            if item.case_id == case_id
        ),
        None
    )

    if authority is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "The recorded comparison is missing "
                "the expected precedent."
            )
        )

    return ComparisonSide(
        validity_status=authority.validity_status,
        judicial_treatment_summary=(
            authority.judicial_treatment_summary
        ),
        authority_assessment=authority.authority_assessment,
        conflicts_or_distinctions=(
            result.authority_comparison.conflicts_or_distinctions
            or ""
        ),
        conclusion=result.conclusion
    )


@router.get(
    "/compare",
    response_model=ExperimentComparisonResponse,
    summary="Compare baseline and treatment-mutation results"
)
def compare_recorded_experiments():
    """
    Compare the actual saved Scenario 1 and
    Scenario 2 responses.

    Shows existing output fields side by side.
    No Gemini request is made.
    """

    baseline = _load_experiment(
        "scenario_1_baseline"
    )

    modified = _load_experiment(
        "scenario_2_treatment_changed"
    )

    case_id = "MOCK_SC_003"

    return ExperimentComparisonResponse(
        mode="recorded",
        comparison_type=(
            "Judicial treatment and validity mutation"
        ),
        compared_case_id=case_id,
        changed_input_metadata=[
            "Judicial treatment: overruled to followed",
            "Validity: no_longer_good_law to good_law",
        ],
        baseline_scenario="scenario_1_baseline",
        modified_scenario="scenario_2_treatment_changed",
        baseline=_comparison_side(baseline.result, case_id),
        modified=_comparison_side(modified.result, case_id),
        note=(
            "These are two previously recorded model outputs. "
            "The endpoint displays existing fields without "
            "generating new reasoning. Treatment and validity "
            "changed together, so this is not an isolated "
            "treatment-label experiment. "
            "All legal evidence is fictional."
        )
    )
