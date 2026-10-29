
"""
Day 2 - Structured Cross-Case Reasoning Test

Runs Component C using the improved:
- Structured Context Builder
- Authority-aware reasoning prompt
- AuthorityComparison output model

Saves the result separately from Day 1.
"""

from pathlib import Path

from reasoning.input_models import ReasoningRequest
from reasoning.gemini_provider import GeminiProvider
from reasoning.reasoning_service import run_cross_case_reasoning


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR / "reasoning" / "data" / "mock_case_data.json"
)

OUTPUT_FILE = (
    BASE_DIR / "outputs" / "day2_structured_reasoning.json"
)


def main():

    print("Starting Day 2 structured legal reasoning...")

    # 1. Load and validate the fictional evidence
    request = ReasoningRequest.model_validate_json(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    print(f"Loaded {len(request.precedents)} precedents.")

    # 2. Initialize Gemini
    provider = GeminiProvider()

    print(f"Using model: {provider.model}")

    # 3. Run reasoning and automatic grounding validation
    result = run_cross_case_reasoning(
        request=request,
        provider=provider
    )

    # 4. Save the complete response
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8"
    )

    print("\nREASONING COMPLETED")

    # 5. Display the structured comparison
    print("\n===== AUTHORITY COMPARISON =====")

    comparison = result.authority_comparison

    comparison_fields = {
        "HIERARCHY": comparison.hierarchy_considerations,
        "CHRONOLOGY": comparison.chronology_considerations,
        "JUDICIAL TREATMENT": (
            comparison.judicial_treatment_considerations
        ),
        "CONFLICTS / DISTINCTIONS": (
            comparison.conflicts_or_distinctions
        ),
    }

    for label, value in comparison_fields.items():

        print(f"\n{label}:")

        if isinstance(value, str) and value.strip():
            print(value)
        else:
            print("[NOT POPULATED]")

    # 6. Check whether all four fields contain text
    populated_count = sum(
        isinstance(value, str) and bool(value.strip())
        for value in comparison_fields.values()
    )

    print(
        f"\nComparison fields populated: "
        f"{populated_count}/4"
    )

    # 7. Display the conclusion
    print("\n===== CONCLUSION =====")
    print(result.conclusion)

    print("\n===== RESULT FILE =====")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
