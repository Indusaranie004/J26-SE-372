
"""
Component C - Function 2
First Legal Brief Generation Experiment

Uses:
1. Original fictional Scenario 1 evidence
2. Previously recorded Function 1 reasoning
3. Gemini-based structured brief generation
4. Brief grounding validation

Default: offline preparation only
--live: send a real Gemini request

Existing generated results are not overwritten.
"""

import argparse
import json
from pathlib import Path

from brief.input_models import BriefGenerationRequest
from brief.context_builder import build_brief_context

from reasoning.output_models import ReasoningResponse

from scripts.run_day2_experiments import load_scenario


BASE_DIR = Path(__file__).resolve().parents[1]

REASONING_FILE = (
    BASE_DIR
    / "data"
    / "demo"
    / "live_experiments"
    / "scenario_1_baseline_response.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "brief_experiments"
    / "baseline_legal_brief.json"
)


def prepare_brief_request() -> BriefGenerationRequest:
    """
    Combine original legal evidence with its
    corresponding recorded Function 1 analysis.
    """

    # Load original fictional scenario
    source_request = load_scenario(
        "scenario_1_baseline"
    )

    # Check recorded reasoning exists
    if not REASONING_FILE.is_file():
        raise FileNotFoundError(
            f"Reasoning response not found: {REASONING_FILE}"
        )

    # Load previously generated reasoning
    reasoning_result = ReasoningResponse.model_validate_json(
        REASONING_FILE.read_text(encoding="utf-8")
    )

    # Verify that both inputs use the same case IDs
    source_ids = {
        case.case_id
        for case in source_request.precedents
    }

    reasoning_ids = {
        case.case_id
        for case in reasoning_result.authorities
    }

    if source_ids != reasoning_ids:
        raise ValueError(
            "Source evidence and recorded reasoning "
            "contain different precedent IDs."
        )

    # Verify recorded validity metadata
    for precedent in source_request.precedents:

        authority = next(
            item
            for item in reasoning_result.authorities
            if item.case_id == precedent.case_id
        )

        expected_validity = (
            precedent.validity.status
            if precedent.validity
            else "unknown"
        )

        if authority.validity_status != expected_validity:
            raise ValueError(
                "Validity metadata mismatch for "
                + precedent.case_id
            )

    return BriefGenerationRequest(
        source_request=source_request,
        reasoning_result=reasoning_result,
        title="Business Permit Revocation - Legal Research Brief"
    )


def main():

    parser = argparse.ArgumentParser(
        description="Function 2 legal brief experiment"
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Generate a real legal brief using Gemini"
    )

    args = parser.parse_args()

    print("COMPONENT C - FUNCTION 2 EXPERIMENT")
    print("=" * 55)

    # Prepare input using existing evidence
    request = prepare_brief_request()

    # Check context builder works
    context = build_brief_context(request)
    context_data = json.loads(context)

    print("Brief title:", request.title)
    print("Legal question:", request.source_request.query)
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
    print("Context prepared:", bool(context_data))
    print("Output file:", OUTPUT_FILE)

    # Default: no API request
    if not args.live:
        print("\nDRY RUN COMPLETED")
        print("Original evidence and reasoning loaded.")
        print("No Gemini API request was made.")
        return

    # Protect existing results
    if OUTPUT_FILE.exists():
        print("\n[SKIPPED] Existing legal brief:")
        print(OUTPUT_FILE)
        return

    # Only import Gemini during live execution
    from brief.brief_provider import GeminiBriefProvider
    from brief.brief_service import run_legal_brief_generation

    provider = GeminiBriefProvider()

    print(f"\nLIVE MODE - Model: {provider.model}")
    print("[RUNNING] Legal brief generation")

    # Generate and validate the legal brief
    result = run_legal_brief_generation(
        request=request,
        provider=provider
    )

    # Only save successfully validated results
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8"
    )

    # Count claims and their evidence references
    sections = [
        "relevant_facts",
        "applicable_legislation",
        "relevant_precedents",
        "precedent_treatment",
        "legal_analysis",
        "arguments",
        "counterarguments",
        "application_to_facts",
        "conclusion",
    ]

    claims = [
        claim
        for section in sections
        for claim in getattr(result, section)
    ]

    reference_count = sum(
        len(claim.evidence_references)
        for claim in claims
    )

    print("\n[SAVED]", OUTPUT_FILE)
    print("Total claims:", len(claims))
    print("Evidence references:", reference_count)
    print("Document type:", result.document_type)
    print("Grounding reference checks: PASSED")

    print("\nEXPERIMENT COMPLETED")


if __name__ == "__main__":
    main()
