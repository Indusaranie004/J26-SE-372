
"""
Day 2 - Controlled Legal Reasoning Experiment Runner

Supports:
- Offline experiment inspection (default)
- Optional live Gemini execution
- Independent scenario outputs
- Custom output directories
- Protection against overwriting previous results

Component C - Function 1

All scenarios use fictional development data.
"""

import argparse
from pathlib import Path

from reasoning.input_models import ReasoningRequest


# ---------------------------------------------
# Project paths
# ---------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

SCENARIO_DIR = BASE_DIR / "outputs" / "day2_scenarios"

RESULT_DIR = BASE_DIR / "outputs" / "day2_experiments"


SCENARIO_NAMES = [
    "scenario_1_baseline",
    "scenario_2_treatment_changed",
    "scenario_3_hierarchy_changed",
    "scenario_4_insufficient_evidence",
]


# ---------------------------------------------
# Load a prepared scenario
# ---------------------------------------------

def load_scenario(name: str) -> ReasoningRequest:
    """Load and validate a prepared scenario."""

    input_file = SCENARIO_DIR / f"{name}.json"

    if not input_file.exists():
        raise FileNotFoundError(
            f"Scenario not found: {input_file}\n"
            "Run python -m scripts.prepare_day2_scenarios first."
        )

    return ReasoningRequest.model_validate_json(
        input_file.read_text(encoding="utf-8")
    )


# ---------------------------------------------
# Display scenario metadata
# ---------------------------------------------

def display_scenario(name: str, request: ReasoningRequest):
    """Display the metadata supplied to Component C."""

    print(f"\n{'=' * 55}")
    print(name.upper())
    print("=" * 55)

    print("Legal question:", request.query)
    print("Reference date:", request.reference_date)
    print("Precedents:", len(request.precedents))

    for precedent in request.precedents:

        validity = (
            precedent.validity.status
            if precedent.validity
            else "unknown"
        )

        print(
            f"\n  Case: {precedent.case_id}"
            f"\n  Court: {precedent.court}"
            f"\n  Validity: {validity}"
        )

        for treatment in precedent.judicial_treatments:
            print(
                f"  Treatment: "
                f"{treatment.source_case_id} "
                f"--{treatment.status}--> "
                f"{treatment.target_case_id}"
            )


# ---------------------------------------------
# Execute a live experiment
# ---------------------------------------------

def run_live_experiment(
    name,
    request,
    provider,
    output_dir: Path | None = None
):
    """
    Execute one experiment and save its response.

    The output directory is optional so existing
    callers and tests remain compatible.

    Existing results are never overwritten.
    """

    if output_dir is None:
        output_dir = RESULT_DIR

    output_file = output_dir / f"{name}_response.json"

    # Protect existing experiment results
    if output_file.exists():
        print(
            f"\n[SKIPPED] Existing result: {output_file}"
        )
        return

    from reasoning.reasoning_service import (
        run_cross_case_reasoning
    )

    print(f"\n[RUNNING] {name}")

    # Execute the existing Function 1 pipeline
    result = run_cross_case_reasoning(
        request=request,
        provider=provider
    )

    # Create the output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the structured response
    output_file.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8"
    )

    # Count populated comparison fields
    comparison = result.authority_comparison

    populated = sum(
        bool(value and value.strip())
        for value in [
            comparison.hierarchy_considerations,
            comparison.chronology_considerations,
            comparison.judicial_treatment_considerations,
            comparison.conflicts_or_distinctions,
        ]
    )

    print(f"[SAVED] {output_file}")
    print(f"Comparison fields populated: {populated}/4")


# ---------------------------------------------
# Main command-line program
# ---------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Day 2 legal reasoning experiments"
    )

    # Enable actual Gemini requests
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable real Gemini API requests"
    )

    # Choose a specific scenario or all four
    parser.add_argument(
        "--scenario",
        choices=["all"] + SCENARIO_NAMES,
        default="all",
        help="Select a specific scenario"
    )

    # Optionally save results in a separate folder
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULT_DIR,
        help=(
            "Directory for saved experiment responses. "
            "Existing response files will not be overwritten."
        )
    )

    args = parser.parse_args()

    selected_names = (
        SCENARIO_NAMES
        if args.scenario == "all"
        else [args.scenario]
    )

    print("COMPONENT C - DAY 2 EXPERIMENT RUNNER")

    # Validate selected scenario inputs
    scenarios = {
        name: load_scenario(name)
        for name in selected_names
    }

    # Display each selected scenario
    for name, request in scenarios.items():
        display_scenario(name, request)

    # Dry run: do not contact Gemini
    if not args.live:
        print("\nDRY RUN COMPLETED")
        print("All selected scenario inputs are valid.")
        print("No Gemini API requests were made.")
        return

    # Initialize Gemini only when live mode is enabled
    from reasoning.gemini_provider import GeminiProvider

    provider = GeminiProvider()

    print(f"\nLIVE MODE - Model: {provider.model}")
    print(f"Result directory: {args.output_dir.resolve()}")

    # Execute experiments inside the chosen folder
    for name, request in scenarios.items():
        run_live_experiment(
            name,
            request,
            provider,
            args.output_dir
        )

    print("\nEXPERIMENT EXECUTION COMPLETED")


# ---------------------------------------------
# Script entry point
# ---------------------------------------------

if __name__ == "__main__":
    main()
