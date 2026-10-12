
"""
Controlled judicial-treatment experiment for Component C.

Tests whether changing an authority's treatment
and validity metadata changes the LLM analysis.

All cases and legal principles are fictional.
"""

from pathlib import Path

from reasoning.input_models import ReasoningRequest
from reasoning.output_models import ReasoningResponse
from reasoning.gemini_provider import GeminiProvider
from reasoning.reasoning_service import run_cross_case_reasoning


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR / "reasoning" / "data" / "mock_case_data.json"
)

OUTPUT_DIR = BASE_DIR / "outputs"

BASELINE_FILE = (
    OUTPUT_DIR / "first_reasoning_response.json"
)

VARIANT_INPUT_FILE = (
    OUTPUT_DIR / "treatment_variant_input.json"
)

VARIANT_OUTPUT_FILE = (
    OUTPUT_DIR / "treatment_variant_response.json"
)


def find_authority(response, case_id):
    return next(
        item for item in response.authorities
        if item.case_id == case_id
    )


def main():

    print("Starting controlled treatment experiment...")

    # load the original input
    original = ReasoningRequest.model_validate_json(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    # Load the existing Gemini baseline output
    if not BASELINE_FILE.exists():
        raise FileNotFoundError(
            "Baseline output not found. Run the original "
            "reasoning pipeline before this experiment."
        )

    baseline = ReasoningResponse.model_validate_json(
        BASELINE_FILE.read_text(encoding="utf-8")
    )

    # deep copy the request to preserve original test data
    variant = original.model_copy(deep=True)

    # select the authority whose status we are changing
    precedent = next(
        p for p in variant.precedents
        if p.case_id == "MOCK_SC_003"
    )

    # change the judicial-treatment relationship
    treatment = next(
        t for t in precedent.judicial_treatments
        if t.source_case_id == "MOCK_SC_006"
    )

    assert treatment.status == "overruled"
    assert precedent.validity.status == "no_longer_good_law"

    treatment.status = "followed"
    treatment.scope = (
        "Administrative discretion in permit revocation"
    )
    treatment.evidence = (
        "The fictional later decision followed the earlier "
        "approach permitting revocation without a prior hearing."
    )

    # keep validity metadata consistent with treatment
    precedent.validity.status = "good_law"
    precedent.validity.safe_to_cite = True
    precedent.validity.summary = (
        "The supplied fictional metadata now identifies "
        "this authority as good law. Its principle may "
        "conflict with other supplied authorities."
    )

    # save the modified input for reproducibility
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    VARIANT_INPUT_FILE.write_text(
        variant.model_dump_json(indent=2),
        encoding="utf-8"
    )

    # run Gemini using the modified evidence
    provider = GeminiProvider()

    print(f"Using model: {provider.model}")
    print("Running modified precedent scenario...")

    result = run_cross_case_reasoning(
        request=variant,
        provider=provider
    )

    VARIANT_OUTPUT_FILE.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8"
    )

    # compare the authority assessments
    baseline_authority = find_authority(
        baseline, "MOCK_SC_003"
    )

    variant_authority = find_authority(
        result, "MOCK_SC_003"
    )

    print("\nEXPERIMENT COMPARISON")

    print("\nBaseline validity:")
    print(baseline_authority.validity_status)

    print("\nVariant validity:")
    print(variant_authority.validity_status)

    print("\nBaseline authority assessment:")
    print(baseline_authority.authority_assessment)

    print("\nVariant authority assessment:")
    print(variant_authority.authority_assessment)

    print("\nVariant cross-case analysis:")
    print(result.cross_case_analysis)

    print("\nOriginal mock dataset was not modified.")
    print(f"Variant input saved to: {VARIANT_INPUT_FILE}")
    print(f"Variant output saved to: {VARIANT_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
