
"""
Component C - FastAPI Application

Function 1:
Cross-Case Contextual and Precedent-Aware Legal Reasoning.

Function 2:
Evidence-Grounded Legal Brief Generation.

Component B Integration:
Accept graph-based precedent clusters, normalize
them, and execute Function 1 reasoning.

For PP1, Component B does not provide judgment
passage text. Legal conclusions must therefore
remain limited to the supplied metadata.
"""

import logging

from google.genai import errors as genai_errors

from typing import Literal

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
)

from pydantic import (
    BaseModel,
    ValidationError,
)

from reasoning.input_models import ReasoningRequest
from reasoning.output_models import ReasoningResponse
from reasoning.llm_provider import LLMProvider
from reasoning.gemini_provider import GeminiProvider
from reasoning.reasoning_service import (
    run_cross_case_reasoning,
)

from integration.component_b_models import (
    ComponentBReasoningRequest,
)
from integration.component_b_adapter import (
    component_b_to_reasoning_request,
)

from api.recorded_demo import (
    router as recorded_demo_router,
)
from api.readable_demo import (
    router as readable_demo_router,
)
from api.experiment_demo import (
    router as experiment_demo_router,
)
from api.brief_api import (
    router as brief_router,
    get_brief_provider,
    generate_legal_brief,
)

from brief.input_models import (
    BriefGenerationRequest,
)

from brief.output_models import (
    LegalBrief,
)


# ---------------------------------------------
# Application setup
# ---------------------------------------------

logger = logging.getLogger(__name__)

app = FastAPI(
    title=(
        "Component C - Legal Reasoning "
        "and Brief Generation API"
    ),
    description=(
        "PP1 prototype for contextual legal reasoning "
        "and evidence-grounded legal brief generation. "
        "Component B integration currently uses graph "
        "metadata without judgment passage retrieval. "
        "Development scenarios use fictional evidence. "
        "Generated conclusions are not independently "
        "verified legal advice."
    ),
    version="0.2.0",
)


# ---------------------------------------------
# Existing API routers
# ---------------------------------------------

app.include_router(recorded_demo_router)
app.include_router(readable_demo_router)
app.include_router(experiment_demo_router)
app.include_router(brief_router)


# ---------------------------------------------
# Function 1 provider dependency
# ---------------------------------------------

def get_llm_provider() -> LLMProvider:
    """
    Create the configured Function 1 provider.

    Tests may inject a fake provider without
    contacting Gemini.
    """

    try:
        return GeminiProvider()

    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The LLM provider is not configured. "
                "Check the Gemini API key."
            ),
        ) from exc


# ---------------------------------------------
# Health check
# ---------------------------------------------

@app.get("/health")
def health_check():
    """
    Check whether the API is running.

    Does not contact Gemini.
    """

    return {
        "status": "ok",
        "component": "Component C",
        "function": (
            "Cross-Case Contextual Legal Reasoning"
        ),
    }


# ---------------------------------------------
# Function 1 reasoning endpoint
# ---------------------------------------------

@app.post(
    "/api/reasoning/analyze",
    response_model=ReasoningResponse,
)
def analyze_legal_scenario(
    request: ReasoningRequest,
    provider: LLMProvider = Depends(get_llm_provider),
) -> ReasoningResponse:
    """
    Analyze supplied legal evidence.

    1. Build structured context.
    2. Generate cross-case reasoning.
    3. Validate structured output.
    4. Check evidence references.
    5. Return validated reasoning.
    """

    try:
        return run_cross_case_reasoning(
            request=request,
            provider=provider,
        )

    # Gemini service errors
    except genai_errors.APIError as exc:

        provider_status = getattr(
            exc,
            "code",
            None,
        )

        logger.warning(
            "LLM provider request failed. Status: %s",
            provider_status,
        )

        if provider_status in {
            429, 500, 502, 503, 504
        }:
            raise HTTPException(
                status_code=503,
                detail=(
                    "The language model service is "
                    "temporarily unavailable. "
                    "Please try again later."
                ),
            ) from exc

        raise HTTPException(
            status_code=502,
            detail=(
                "The language model provider "
                "rejected the request."
            ),
        ) from exc

    # Invalid reasoning or evidence references
    except (ValidationError, ValueError) as exc:

        logger.warning(
            "Reasoning output validation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "The generated reasoning did not "
                "pass structured output or "
                "grounding validation."
            ),
        ) from exc

    # Empty or unusable LLM response
    except RuntimeError as exc:

        logger.warning(
            "Reasoning generation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "The language model did not return "
                "a usable reasoning response."
            ),
        ) from exc


# ---------------------------------------------
# NEW: Component B -> Function 1 integration
# ---------------------------------------------

@app.post(
    "/api/integration/component-b/reasoning",
    response_model=ReasoningResponse,
    tags=["Component B Integration"],
    summary=(
        "Analyze Component B precedent clusters"
    ),
    description=(
        "Accepts Component B's PP1 graph-based "
        "precedent clusters, converts them to a "
        "Component C ReasoningRequest, and executes "
        "Function 1. Judgment passage text is not "
        "provided by Component B at PP1. "
        "The result is preliminary metadata-based "
        "analysis, not a verified interpretation "
        "of the underlying judgments."
    ),
)
def analyze_component_b_clusters(
    request: ComponentBReasoningRequest,
    provider: LLMProvider = Depends(get_llm_provider),
) -> ReasoningResponse:
    """
    Run Component B -> Component C integration.

    Pipeline:
        Component B clusters
        -> Input adapter
        -> ReasoningRequest
        -> Function 1
        -> ReasoningResponse

    This endpoint does not run Function 2 yet.
    """

    try:
        reasoning_request = (
            component_b_to_reasoning_request(request)
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    # Reuse the existing Function 1 endpoint logic,
    # including its provider error handling and
    # grounding validation.
    return analyze_legal_scenario(
        request=reasoning_request,
        provider=provider,
    )


# ---------------------------------------------
# Component B -> Function 1 -> Function 2
# ---------------------------------------------

METADATA_ONLY_NOTICE = (
    "This preliminary legal research brief is based "
    "on Component B's retrieved graph metadata. "
    "Judgment passage text and statutory wording "
    "were not supplied. Citation relationships and "
    "legislation identifiers do not independently "
    "establish the substantive legal holdings or "
    "meaning of the referenced authorities. "
    "Original sources require human verification."
)


class ComponentBPipelineResponse(BaseModel):
    """
    Combined Function 1 and Function 2 output.

    The response explicitly identifies the
    metadata-only evidence boundary.
    """

    evidence_mode: Literal["metadata_only"]

    note: str

    reasoning: ReasoningResponse

    legal_brief: LegalBrief


@app.post(
    "/api/integration/component-b/brief",
    response_model=ComponentBPipelineResponse,
    tags=["Component B Integration"],
    summary=(
        "Generate legal reasoning and brief "
        "from Component B clusters"
    ),
)
def generate_component_b_legal_brief(
    request: ComponentBReasoningRequest,
    provider: LLMProvider = Depends(get_llm_provider),
    brief_provider: LLMProvider = Depends(
        get_brief_provider
    ),
    title: str = Query(
        default="Component B Metadata Legal Research Brief",
        min_length=1,
    ),
) -> ComponentBPipelineResponse:
    """
    Full Component C PP1 integration.

    Pipeline:

        Component B JSON
            -> Component B adapter
            -> Function 1 reasoning
            -> Function 2 legal brief
            -> Combined response

    The generated result is preliminary because
    the PP1 Component B interface does not
    contain judgment passage text.

    Existing Function 1 and Function 2 endpoint
    handlers are reused with explicitly supplied
    providers, preserving their established
    validation and error handling.
    """

    # -----------------------------------------
    # 1. Normalize Component B's clusters
    # -----------------------------------------

    try:
        reasoning_request = (
            component_b_to_reasoning_request(
                request
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    # -----------------------------------------
    # 2. Execute Function 1
    # -----------------------------------------

    reasoning_result = analyze_legal_scenario(
        request=reasoning_request,
        provider=provider,
    )

    # Preserve the metadata-only limitation
    # independently of Gemini's wording.

    reasoning_limitations = list(
        reasoning_result.limitations_or_insufficient_evidence
    )

    if METADATA_ONLY_NOTICE not in reasoning_limitations:
        reasoning_limitations.append(
            METADATA_ONLY_NOTICE
        )

    reasoning_result = reasoning_result.model_copy(
        update={
            "limitations_or_insufficient_evidence": (
                reasoning_limitations
            )
        }
    )

    # -----------------------------------------
    # 3. Prepare Function 2 input
    # -----------------------------------------

    brief_request = BriefGenerationRequest(
        source_request=reasoning_request,
        reasoning_result=reasoning_result,
        title=title,
    )

    # -----------------------------------------
    # 4. Execute Function 2
    # -----------------------------------------

    legal_brief = generate_legal_brief(
        request=brief_request,
        provider=brief_provider,
    )

    # -----------------------------------------
    # 5. Preserve evidence limitations
    # -----------------------------------------

    brief_limitations = list(
        legal_brief.limitations
    )

    if METADATA_ONLY_NOTICE not in brief_limitations:
        brief_limitations.append(
            METADATA_ONLY_NOTICE
        )

    legal_brief = legal_brief.model_copy(
        update={
            "limitations": brief_limitations
        }
    )

    # -----------------------------------------
    # 6. Return both generated results
    # -----------------------------------------

    return ComponentBPipelineResponse(
        evidence_mode="metadata_only",
        note=METADATA_ONLY_NOTICE,
        reasoning=reasoning_result,
        legal_brief=legal_brief,
    )

