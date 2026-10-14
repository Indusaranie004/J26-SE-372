
"""
Component C - FastAPI Application

Exposes Function 1:
Cross-Case Contextual & Precedent-Aware Legal Reasoning.

The API delegates legal reasoning to the existing
reasoning service instead of implementing it here.
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
    run_cross_case_reasoning
)
from api.recorded_demo import router as recorded_demo_router
from api.readable_demo import router as readable_demo_router


# ---------------------------------------------
# Application setup
# ---------------------------------------------

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Component C - Legal Reasoning API",
    description=(
        "PP1 prototype for evidence-grounded, "
        "cross-case contextual legal reasoning. "
        "Development scenarios use fictional legal data."
    ),
    version="0.1.0"
)

# Register the recorded demonstration endpoint
app.include_router(recorded_demo_router)

# Human-readable recorded demonstration
app.include_router(readable_demo_router)


# ---------------------------------------------
# LLM provider dependency
# ---------------------------------------------

def get_llm_provider() -> LLMProvider:
    """
    Create the configured LLM provider.

    Keeping this separate makes it possible
    to replace the provider or use a fake
    provider during automated tests.
    """

    try:
        return GeminiProvider()

    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The LLM provider is not configured. "
                "Check the Gemini API key."
            )
        ) from exc


# ---------------------------------------------
# Health check
# ---------------------------------------------

@app.get("/health")
def health_check():
    """
    Check whether the API is running.

    This does not contact Gemini.
    """

    return {
        "status": "ok",
        "component": "Component C",
        "function": "Cross-Case Contextual Legal Reasoning"
    }


# ---------------------------------------------
# Legal reasoning endpoint
# ---------------------------------------------

@app.post(
    "/api/reasoning/analyze",
    response_model=ReasoningResponse
)
def analyze_legal_scenario(
    request: ReasoningRequest,
    provider: LLMProvider = Depends(get_llm_provider)
) -> ReasoningResponse:
    """
    Analyze supplied fictional legal evidence.

    Steps performed by the existing service:
    1. Build structured context
    2. Generate reasoning using the provider
    3. Parse the structured response
    4. Validate evidence references
    5. Return the validated result
    """

    try:
        result = run_cross_case_reasoning(
            request=request,
            provider=provider
        )

        return result

    # -----------------------------------------
    # Gemini API errors
    # -----------------------------------------

    except genai_errors.APIError as exc:

        provider_status = getattr(exc, "code", None)

        logger.warning(
            "LLM provider request failed. Status: %s",
            provider_status
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
                )
            ) from exc

        raise HTTPException(
            status_code=502,
            detail=(
                "The language model provider "
                "rejected the request."
            )
        ) from exc

    # -----------------------------------------
    # Invalid structured reasoning output
    # -----------------------------------------

    except (ValidationError, ValueError) as exc:

        logger.warning(
            "Reasoning output validation failed: %s",
            exc
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "The generated reasoning did not "
                "pass structured output or "
                "grounding validation."
            )
        ) from exc

    # -----------------------------------------
    # Empty or unusable provider response
    # -----------------------------------------

    except RuntimeError as exc:

        logger.warning(
            "Reasoning generation failed: %s",
            exc
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "The language model did not return "
                "a usable reasoning response."
            )
        ) from exc
