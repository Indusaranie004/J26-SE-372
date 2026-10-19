
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

from fastapi import Depends, FastAPI, HTTPException
from google.genai import errors as genai_errors
from pydantic import ValidationError

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
