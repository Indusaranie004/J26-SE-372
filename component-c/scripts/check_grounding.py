
"""
Check the grounding of the saved reasoning output
"""

from pathlib import Path

from reasoning.input_models import ReasoningRequest
from reasoning.output_models import ReasoningResponse
from reasoning.grounding_validator import validate_grounding


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR / "reasoning" / "data" / "mock_case_data.json"
)

OUTPUT_FILE = (
    BASE_DIR / "outputs" / "first_reasoning_response.json"
)


def main():

    request = ReasoningRequest.model_validate_json(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    response = ReasoningResponse.model_validate_json(
        OUTPUT_FILE.read_text(encoding="utf-8")
    )

    errors = validate_grounding(request, response)

    print("\nEVIDENCE GROUNDING CHECK")

    if errors:
        print(f"\nFound {len(errors)} issue(s):")

        for error in errors:
            print(f"- {error}")
    else:
        print("\nAll grounding checks passed!")

    print("\nAuthorities analyzed:", len(response.authorities))


if __name__ == "__main__":
    main()
