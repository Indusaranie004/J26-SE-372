
"""
Day 2 - Controlled Legal Reasoning Scenarios

Creates fictional test scenarios for evaluating
Component C's contextual reasoning.

No LLM API calls are made.
"""

from pathlib import Path

from reasoning.input_models import ReasoningRequest


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR / "reasoning" / "data" / "mock_case_data.json"
)

OUTPUT_DIR = BASE_DIR / "outputs" / "day2_scenarios"


def load_original_request() -> ReasoningRequest:
    """Load and validate the original mock evidence."""

    return ReasoningRequest.model_validate_json(
        INPUT_FILE.read_text(encoding="utf-8")
    )


def create_scenarios() -> dict[str, ReasoningRequest]:
    """Prepare independent controlled scenarios."""

    original = load_original_request()

    scenarios = {}

    # --------------------------------------------
    # SCENARIO 1: Original baseline
    # --------------------------------------------

    scenarios["scenario_1_baseline"] = (
        original.model_copy(deep=True)
    )

    # --------------------------------------------
    # SCENARIO 2: Judicial treatment mutation
    # --------------------------------------------

    treatment_variant = original.model_copy(deep=True)

    precedent = next(
        p for p in treatment_variant.precedents
        if p.case_id == "MOCK_SC_003"
    )

    treatment = precedent.judicial_treatments[0]

    # Change the supplied treatment
    treatment.status = "followed"

    treatment.evidence = (
        "The fictional later decision followed the "
        "earlier approach to discretionary permit "
        "revocation."
    )

    # Update associated validity metadata to keep
    # the fictional scenario internally consistent.
    precedent.validity.status = "good_law"
    precedent.validity.safe_to_cite = True

    precedent.validity.summary = (
        "The fictional metadata now identifies "
        "the precedent as good law."
    )

    scenarios["scenario_2_treatment_changed"] = (
        treatment_variant
    )

    # --------------------------------------------
    # SCENARIO 3: Court hierarchy mutation
    # --------------------------------------------

    hierarchy_variant = original.model_copy(deep=True)

    precedent = next(
        p for p in hierarchy_variant.precedents
        if p.case_id == "MOCK_CA_002"
    )

    # Synthetic hierarchy experiment.
    # Keep the stable internal case ID for pairing
    # the before-and-after responses.
    precedent.court = "Supreme Court"

    precedent.case_number = "MOCK/SC/002/2018"

    scenarios["scenario_3_hierarchy_changed"] = (
        hierarchy_variant
    )

    # --------------------------------------------
    # SCENARIO 4: Insufficient relevant evidence
    # --------------------------------------------

    insufficient_variant = original.model_copy(deep=True)

    insufficient_variant.query = (
        "Based only on the supplied authorities, "
        "is the business entitled to financial "
        "compensation for lost income following "
        "the permit revocation?"
    )

    # The existing evidence concerns procedural
    # fairness, not financial compensation.

    scenarios["scenario_4_insufficient_evidence"] = (
        insufficient_variant
    )

    return scenarios


def main():

    print("Preparing Day 2 reasoning scenarios...")

    scenarios = create_scenarios()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for scenario_name, request in scenarios.items():

        output_file = (
            OUTPUT_DIR / f"{scenario_name}.json"
        )

        # Validate the generated request again
        validated = ReasoningRequest.model_validate(
            request.model_dump()
        )

        output_file.write_text(
            validated.model_dump_json(indent=2),
            encoding="utf-8"
        )

        print(
            f"[CREATED] {scenario_name} "
            f"({len(validated.precedents)} precedents)"
        )

    print("\nAll scenarios generated successfully.")
    print(f"Saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
