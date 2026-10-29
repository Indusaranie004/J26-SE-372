
"""
Component C - Function 2
Legal Brief Generation Service

Coordinates:
1. Brief context preparation
2. LLM-based brief generation
3. Pydantic structured-output validation
4. Requested document title validation

Claim-level evidence grounding will be
implemented separately.
"""

from reasoning.llm_provider import LLMProvider

from brief.input_models import BriefGenerationRequest
from brief.output_models import LegalBrief
from brief.context_builder import build_brief_context
from brief.brief_prompt import LEGAL_BRIEF_SYSTEM_PROMPT
from brief.grounding_validator import validate_brief_grounding


def run_legal_brief_generation(
    request: BriefGenerationRequest,
    provider: LLMProvider
) -> LegalBrief:
    """
    Generate and structurally validate
    a legal research brief.

    Args:
        request:
            Original evidence and Function 1 reasoning.

        provider:
            An LLM provider supporting generate().

    Returns:
        A validated LegalBrief object.

    Note:
        This stage does not yet verify whether
        every cited source exists or semantically
        supports its associated claim.
    """

    # -----------------------------------------
    # 1. Build the legal brief context
    # -----------------------------------------

    context = build_brief_context(request)

    # -----------------------------------------
    # 2. Generate a legal brief
    # -----------------------------------------

    raw_response = provider.generate(
        system_prompt=LEGAL_BRIEF_SYSTEM_PROMPT,
        user_prompt=context
    )

    # -----------------------------------------
    # 3. Validate structured output
    # -----------------------------------------

    brief = LegalBrief.model_validate_json(
        raw_response
    )

    # -----------------------------------------
    # 4. Check requested title consistency
    # -----------------------------------------

    if brief.title != request.title:
        raise ValueError(
            "The generated legal brief title "
            "does not match the requested title."
        )

    # -----------------------------------------
    # 5. Validate claim-level evidence references
    # -----------------------------------------

    grounding_errors = validate_brief_grounding(
        request,
        brief
    )

    if grounding_errors:

        details = "\n".join(
            f"- {error}"
            for error in grounding_errors
        )

        raise ValueError(
            "Brief grounding validation failed:\n"
            + details
        )

    # -----------------------------------------
    # 6. Return the validated brief
    # -----------------------------------------

    return brief
