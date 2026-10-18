
"""
Component C - Function 2
Insufficient-Evidence Legal Brief Experiment

Tests whether legal brief generation preserves
uncertainty when supplied legal authorities
do not establish the requested remedy.

Uses:
- Function 1 Scenario 4 input
- Recorded Function 1 Scenario 4 reasoning
- Function 2 Gemini brief generation

Default: offline preparation
--live: run Gemini generation

This experiment uses fictional legal data.
"""

import argparse
from pathlib import Path

from scripts.run_day2_experiments import load_scenario

from reasoning.output_models import ReasoningResponse

from brief.input_models import BriefGenerationRequest
from brief.context_builder import build_brief_context


BASE_DIR = Path(__file__).resolve().parents[1]

SCENARIO_NAME = "scenario_4_insufficient_evidence"

REASONING_FILE = (
    BASE_DIR
    / "data"
    / "demo"
    / "live_experiments"
    / "scenario_4_insufficient_evidence_response.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "brief_experiments"
    / "insufficient_evidence_legal_brief.json"
)


def prepare_request() -> BriefGenerationRequest:
    """
    Load the original insufficient-evidence
    scenario and its Function 1 analysis.
    """

    source_request = load_scenario(
        SCENARIO_NAME
    )

    if not REASONING_FILE.is_file():
        raise FileNotFoundError(
            f"Missing Function 1 output: {REASONING_FILE}"
        )

    reasoning_result = ReasoningResponse.model_validate_json(
        REASONING_FILE.read_text(
            encoding="utf-8"
        )
    )

    # Ensure the reasoning references only
    # cases supplied with this scenario.
    source_ids = {
        precedent.case_id
        for precedent in source_request.precedents
    }

    reasoning_ids = {
        authority.case_id
        for authority in reasoning_result.authorities
    }

    unknown_ids = reasoning_ids - source_ids

    if unknown_ids:
        raise ValueError(
            "Function 1 reasoning contains "
            "unknown authorities: "
            + ", ".join(sorted(unknown_ids))
        )

    return BriefGenerationRequest(
        source_request=source_request,
        reasoning_result=reasoning_result,
        title=(
            "Compensation for Lost Income "
            "- Evidence-Limited Legal Research Brief"
        )
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run Function 2 insufficient-evidence experiment"
        )
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Call Gemini to generate a new legal brief"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("FUNCTION 2 - INSUFFICIENT EVIDENCE EXPERIMENT")
    print("=" * 60)

    request = prepare_request()

    context = build_brief_context(
        request
    )

    print("Title:", request.title)
    print("Question:", request.source_request.query)

    print(
        "Precedents:",
        len(request.source_request.precedents)
    )

    print(
        "Case facts:",
        len(request.source_request.case_facts)
    )

    print(
        "Reasoning authorities:",
        len(request.reasoning_result.authorities)
    )

    print(
        "Context prepared:",
        bool(context)
    )

    print(
        "\nFunction 1 conclusion:",
        request.reasoning_result.conclusion
    )

    if not args.live:

        print("\nDRY RUN COMPLETED")
        print("No Gemini API request was made.")
        return

    if OUTPUT_FILE.exists():

        print("\n[SKIPPED] Output already exists:")
        print(OUTPUT_FILE)
        return

    from brief.brief_provider import GeminiBriefProvider

    from brief.brief_service import (
        run_legal_brief_generation
    )

    provider = GeminiBriefProvider()

    print("\nModel:", provider.model)
    print("[RUNNING] Generating legal brief...")

    result = run_legal_brief_generation(
        request=request,
        provider=provider
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8"
    )

    print("\n[SAVED]", OUTPUT_FILE)

    print("\nLEGAL ANALYSIS")

    for claim in result.legal_analysis:
        print(
            f"[{claim.support_status}] "
            f"{claim.statement}"
        )

    print("\nCONCLUSION")

    for claim in result.conclusion:
        print(
            f"[{claim.support_status}] "
            f"{claim.statement}"
        )

    print("\nLIMITATIONS")

    for limitation in result.limitations:
        print("-", limitation)

    print("\nEXPERIMENT COMPLETED")
    print(
        "Note: Reference validation passed, "
        "but semantic support must be reviewed."
    )


if __name__ == "__main__":
    main()
