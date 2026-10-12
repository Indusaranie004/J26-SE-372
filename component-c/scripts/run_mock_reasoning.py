
"""
Run Component C Function 1 using fictional precedents.
"""

import json
from pathlib import Path

from reasoning.input_models import ReasoningRequest
from reasoning.gemini_provider import GeminiProvider
from reasoning.reasoning_service import run_cross_case_reasoning


# locate component c directory
BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR / "reasoning" / "data" / "mock_case_data.json"
)

OUTPUT_FILE = (
    BASE_DIR / "outputs" / "first_reasoning_response.json"
)


def main():

    print("Starting Component C legal reasoning...")

    # 1. load mock precedent data
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        input_data = json.load(file)

    # 2. validate input
    request = ReasoningRequest.model_validate(input_data)

    print(
        f"Validated {len(request.precedents)} "
        "fictional precedents."
    )

    # 3. initialize Gemini
    provider = GeminiProvider()

    print(f"Using LLM: {provider.model}")

    # 4. Generate contextual legal reasoning
    result = run_cross_case_reasoning(
        request=request,
        provider=provider
    )

    # 5. save structured output
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8"
    )

    # 6. display a summary
    print("\nREASONING COMPLETED")

    print("\nLegal Issue:")
    print(result.legal_issue)

    print("\nAuthorities Analyzed:")
    for authority in result.authorities:
        print(
            f"- {authority.case_id}: "
            f"{authority.validity_status}"
        )

    print("\nConclusion:")
    print(result.conclusion)

    print("\nLimitations:")
    for limitation in result.limitations_or_insufficient_evidence:
        print(f"- {limitation}")

    print(f"\nFull result saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
