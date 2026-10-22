
"""
Component C - Readable Demonstration Endpoint

Displays the previously recorded fictional legal
reasoning response as a human-readable report.

- No Gemini API calls
- No new legal reasoning
- Uses the existing recorded demo
- Preserves the original reasoning content
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from api.recorded_demo import get_recorded_demo

from reasoning.result_formatter import (
    format_reasoning_report
)


router = APIRouter(
    prefix="/api/reasoning/demo",
    tags=["Recorded Demonstrations"]
)


@router.get(
    "/readable",
    response_class=PlainTextResponse,
    summary="View recorded legal reasoning as readable text"
)
def get_readable_demo() -> PlainTextResponse:
    """
    Load the saved demonstration response and
    format it as plain text.

    This does not call the Gemini API.
    """

    # Step 1: Reuse the existing recorded endpoint logic
    recorded = get_recorded_demo()

    # Step 2: Format its validated reasoning result
    report = format_reasoning_report(
        recorded.result
    )

    # Step 3: Clearly identify the source of the report
    header = (
        "DEMONSTRATION MODE: RECORDED\n"
        f"SCENARIO: {recorded.scenario}\n"
        f"NOTE: {recorded.note}\n"
        "\n"
    )

    # Step 4: Return readable text
    return PlainTextResponse(
        content=header + report
    )
