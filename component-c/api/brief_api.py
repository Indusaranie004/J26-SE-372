
"""
Component C - Function 2
Evidence-Grounded Legal Brief API

Endpoints:
GET  /api/brief/demo/recorded
GET  /api/brief/demo/readable
POST /api/brief/generate

The recorded endpoints use saved fictional
development data and do not contact Gemini.

The live endpoint generates a structured
legal research brief from supplied evidence
and Function 1 reasoning.
"""

import logging
from pathlib import Path
from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from fastapi.responses import Response
from google.genai import errors as genai_errors
from pydantic import BaseModel, ValidationError

from reasoning.llm_provider import LLMProvider

from brief.input_models import BriefGenerationRequest
from brief.output_models import LegalBrief
from brief.brief_provider import GeminiBriefProvider
from brief.brief_service import (
    run_legal_brief_generation,
)
from brief.brief_formatter import (
    format_legal_brief,
)
from brief.docx_exporter import (
    export_legal_brief_docx,
)

from brief.pdf_exporter import (
    export_legal_brief_pdf,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/brief",
    tags=["Function 2 - Legal Brief Generation"],
)


# ---------------------------------------------
# Recorded demonstration configuration
# ---------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

RECORDED_BRIEF_FILE = (
    BASE_DIR
    / "data"
    / "demo"
    / "briefs"
    / "improved_baseline_legal_brief.json"
)


class MarkdownResponse(Response):
    """
    Return Markdown text with the appropriate
    HTTP content type.
    """

    media_type = "text/markdown"



class RecordedBriefResponse(BaseModel):
    """
    Distinguishes recorded demonstration
    output from newly generated results.
    """

    mode: Literal["recorded"]

    scenario: str

    note: str

    result: LegalBrief



# ---------------------------------------------
# Gemini provider dependency
# ---------------------------------------------

def get_brief_provider() -> LLMProvider:
    """
    Create the Gemini provider for Function 2.

    Keeping this dependency separate allows
    automated tests to inject a fake provider.
    """

    try:
        return GeminiBriefProvider()

    except ValueError as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "The legal brief generation provider "
                "is not configured. "
                "Check the Gemini API key."
            ),
        ) from exc


# ---------------------------------------------
# Load recorded legal brief
# ---------------------------------------------

def load_recorded_brief() -> LegalBrief:
    """
    Load and structurally validate the saved
    Gemini-generated legal research brief.

    No Gemini request is made.
    """

    if not RECORDED_BRIEF_FILE.is_file():

        raise HTTPException(
            status_code=404,
            detail=(
                "The recorded legal brief was not found."
            ),
        )

    try:

        saved_json = RECORDED_BRIEF_FILE.read_text(
            encoding="utf-8"
        )

        return LegalBrief.model_validate_json(
            saved_json
        )

    except (OSError, ValidationError) as exc:

        logger.warning(
            "Could not load recorded legal brief: %s",
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The recorded legal brief could not "
                "be read or validated."
            ),
        ) from exc


# ---------------------------------------------
# GET: Recorded structured legal brief
# ---------------------------------------------


@router.get(
    "/demo/recorded",
    response_model=RecordedBriefResponse,
    summary="View recorded Gemini-generated legal brief",
)
def get_recorded_brief() -> RecordedBriefResponse:
    """
    Return the improved recorded legal brief.

    This is a recorded demonstration.
    It does not generate a new document
    or contact Gemini.
    """

    brief = load_recorded_brief()

    return RecordedBriefResponse(
        mode="recorded",

        scenario=(
            "Scenario 1 - Fictional permit revocation"
        ),

        note=(
            "This is a previously generated Gemini "
            "legal research brief, not a live response. "
            "It uses fictional development evidence "
            "and includes the improved judicial-treatment "
            "citation mechanism. Its references passed "
            "structural and reference-grounding validation. "
            "The original baseline has been preserved "
            "separately for experimental comparison. "
            "Semantic and legal correctness have not "
            "been independently verified."
        ),

        result=brief,
    )



# ---------------------------------------------
# GET: Human-readable recorded legal brief
# ---------------------------------------------

@router.get(
    "/demo/readable",
    response_class=MarkdownResponse,
    summary="View recorded legal brief as Markdown",
)
def get_readable_brief() -> MarkdownResponse:
    """
    Format the recorded legal brief as Markdown.

    Does not contact Gemini or alter the
    original saved JSON.
    """

    brief = load_recorded_brief()

    report = format_legal_brief(brief)

    demonstration_header = (
        "> **DEMONSTRATION MODE: RECORDED**\n"
        ">\n"
        "> Scenario: Fictional permit revocation\n"
        ">\n"
        "> This document was generated previously. "
        "It is not a new Gemini response, and its "
        "legal conclusions have not been "
        "independently verified.\n\n"
        "---\n\n"
    )

    return MarkdownResponse(
        content=demonstration_header + report
    )


# ---------------------------------------------
# POST: Generate a new legal research brief
# ---------------------------------------------

@router.post(
    "/generate",
    response_model=LegalBrief,
    summary="Generate an evidence-grounded legal brief",
)
def generate_legal_brief(
    request: BriefGenerationRequest,
    provider: LLMProvider = Depends(get_brief_provider),
) -> LegalBrief:
    """
    Generate a structured legal research brief.

    Input:
        Original legal evidence
        Function 1 reasoning result
        Requested document title

    Steps:
        1. Build drafting context
        2. Generate with Gemini
        3. Validate structured output
        4. Validate evidence references
        5. Return the accepted LegalBrief

    The current grounding validator checks
    reference consistency, not semantic entailment.
    """

    try:

        return run_legal_brief_generation(
            request=request,
            provider=provider,
        )

    # -----------------------------------------
    # Gemini service errors
    # -----------------------------------------

    except genai_errors.APIError as exc:

        provider_status = getattr(
            exc,
            "code",
            None,
        )

        logger.warning(
            "Legal brief provider request failed. "
            "Status: %s",
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
                "rejected the legal brief request."
            ),
        ) from exc

    # -----------------------------------------
    # Output or grounding validation errors
    # -----------------------------------------

    except (ValidationError, ValueError) as exc:

        logger.warning(
            "Legal brief validation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "The generated legal brief failed "
                "structured output or evidence "
                "reference validation."
            ),
        ) from exc

    # -----------------------------------------
    # Empty or unusable LLM response
    # -----------------------------------------

    except RuntimeError as exc:

        logger.warning(
            "Legal brief generation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "The language model did not return "
                "a usable legal brief response."
            ),
        ) from exc


# ---------------------------------------------
# Function 2 - Document Download API
# ---------------------------------------------

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)

PDF_MEDIA_TYPE = "application/pdf"


# ---------------------------------------------
# Shared document response helper
# ---------------------------------------------

def _create_document_response(
    brief: LegalBrief,
    file_format: Literal["docx", "pdf"],
) -> Response:
    """
    Convert an existing LegalBrief into a
    downloadable document.

    Supports:
        - DOCX
        - PDF

    No Gemini API calls are made.
    The original LegalBrief is not modified.
    """

    if file_format == "docx":

        file_bytes = export_legal_brief_docx(
            brief
        )

        media_type = DOCX_MEDIA_TYPE

        filename = "legal_research_brief.docx"

    elif file_format == "pdf":

        file_bytes = export_legal_brief_pdf(
            brief
        )

        media_type = PDF_MEDIA_TYPE

        filename = "legal_research_brief.pdf"

    else:

        raise ValueError(
            "Unsupported document format."
        )

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
        },
    )


# ---------------------------------------------
# GET: Download recorded brief as DOCX
# ---------------------------------------------

@router.get(
    "/demo/download/docx",
    response_class=Response,
    tags=["Function 2 - Document Downloads"],
    summary="Download recorded legal brief as Word",
    responses={
        200: {
            "description": "Generated DOCX document",
            "content": {
                DOCX_MEDIA_TYPE: {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def download_recorded_brief_docx() -> Response:
    """
    Download the saved improved baseline
    legal brief as a Word document.

    Does not contact Gemini.
    """

    brief = load_recorded_brief()

    return _create_document_response(
        brief=brief,
        file_format="docx",
    )


# ---------------------------------------------
# GET: Download recorded brief as PDF
# ---------------------------------------------

@router.get(
    "/demo/download/pdf",
    response_class=Response,
    tags=["Function 2 - Document Downloads"],
    summary="Download recorded legal brief as PDF",
    responses={
        200: {
            "description": "Generated PDF document",
            "content": {
                PDF_MEDIA_TYPE: {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def download_recorded_brief_pdf() -> Response:
    """
    Download the saved improved baseline
    legal brief as a PDF document.

    Does not contact Gemini.
    """

    brief = load_recorded_brief()

    return _create_document_response(
        brief=brief,
        file_format="pdf",
    )


# ---------------------------------------------
# POST: Export supplied LegalBrief as DOCX
# ---------------------------------------------

@router.post(
    "/export/docx",
    response_class=Response,
    tags=["Function 2 - Document Downloads"],
    summary="Export LegalBrief JSON as Word",
    responses={
        200: {
            "description": "Generated DOCX document",
            "content": {
                DOCX_MEDIA_TYPE: {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_brief_as_docx(
    brief: LegalBrief,
) -> Response:
    """
    Accept an existing structured LegalBrief
    and export it as a Word document.

    Pydantic validates the brief structure.

    The endpoint does not independently
    verify whether cited evidence supports
    the legal claims.

    No Gemini API calls are made.
    """

    return _create_document_response(
        brief=brief,
        file_format="docx",
    )


# ---------------------------------------------
# POST: Export supplied LegalBrief as PDF
# ---------------------------------------------

@router.post(
    "/export/pdf",
    response_class=Response,
    tags=["Function 2 - Document Downloads"],
    summary="Export LegalBrief JSON as PDF",
    responses={
        200: {
            "description": "Generated PDF document",
            "content": {
                PDF_MEDIA_TYPE: {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_brief_as_pdf(
    brief: LegalBrief,
) -> Response:
    """
    Accept an existing structured LegalBrief
    and export it as a PDF document.

    Pydantic validates the brief structure.

    This endpoint does not perform
    independent legal correctness checks.

    No Gemini API calls are made.
    """

    return _create_document_response(
        brief=brief,
        file_format="pdf",
    )

