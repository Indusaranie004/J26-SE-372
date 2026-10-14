
"""
Component C - Recorded Demonstration Endpoint

Returns a previously generated fictional reasoning response.

Important:
- Does not call Gemini.
- Does not generate new reasoning.
- Clearly identifies the result as recorded.
- Loads a version-controlled demonstration fixture.
"""

import logging

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from reasoning.output_models import ReasoningResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/reasoning/demo",
    tags=["Recorded Demonstrations"]
)


# Locate the component-c project directory
BASE_DIR = Path(__file__).resolve().parents[1]


# Version-controlled fictional Day 1 demonstration result
RECORDED_RESULT_FILE = (
    BASE_DIR
    / "data"
    / "demo"
    / "day1_baseline_response.json"
)


class RecordedDemoResponse(BaseModel):
    """
    Identifies saved reasoning separately from
    newly generated LLM responses.
    """

    mode: Literal["recorded"]

    scenario: str

    note: str

    comparison_available: bool

    result: ReasoningResponse


@router.get(
    "/recorded",
    response_model=RecordedDemoResponse
)
def get_recorded_demo() -> RecordedDemoResponse:
    """
    Load the version-controlled Day 1 baseline.

    No Gemini API request is made.
    """

    if not RECORDED_RESULT_FILE.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "The recorded demonstration result "
                "was not found. Check the demo fixture."
            )
        )

    try:
        saved_json = RECORDED_RESULT_FILE.read_text(
            encoding="utf-8"
        )

        result = ReasoningResponse.model_validate_json(
            saved_json
        )

    except (OSError, ValidationError) as exc:

        logger.warning(
            "Could not load recorded demo: %s",
            exc
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The recorded demonstration file "
                "could not be read or validated."
            )
        ) from exc

    comparison = result.authority_comparison

    comparison_fields = [
        comparison.hierarchy_considerations,
        comparison.chronology_considerations,
        comparison.judicial_treatment_considerations,
        comparison.conflicts_or_distinctions,
    ]

    comparison_available = all(
        isinstance(value, str) and bool(value.strip())
        for value in comparison_fields
    )

    return RecordedDemoResponse(
        mode="recorded",

        scenario=(
            "Day 1 baseline - fictional legal cases"
        ),

        note=(
            "This is a previously generated reasoning "
            "response, not a live Gemini result. "
            "The Day 1 output predates the structured "
            "authority comparison introduced on Day 2. "
            "This response uses fictional development "
            "test data and has not been independently "
            "verified for legal correctness. "
            "It does not constitute legal advice."
        ),

        comparison_available=comparison_available,

        result=result
    )
