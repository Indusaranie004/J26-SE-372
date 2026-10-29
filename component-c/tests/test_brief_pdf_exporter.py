
"""
Component C - Function 2
PDF Export Tests

Uses a previously recorded Gemini legal brief.

No Gemini API calls are made.
"""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from brief.output_models import LegalBrief

from brief.pdf_exporter import (
    export_legal_brief_pdf,
)


BRIEF_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "demo"
    / "briefs"
    / "improved_baseline_legal_brief.json"
)


def load_brief():

    return LegalBrief.model_validate_json(
        BRIEF_PATH.read_text(
            encoding="utf-8"
        )
    )


def read_pdf_text(pdf_bytes):

    reader = PdfReader(
        BytesIO(pdf_bytes)
    )

    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    return reader, text


def test_pdf_export_produces_valid_pdf():

    brief = load_brief()

    pdf_bytes = export_legal_brief_pdf(
        brief
    )

    assert isinstance(pdf_bytes, bytes)

    assert pdf_bytes.startswith(b"%PDF-")

    assert len(pdf_bytes) > 0

    reader, _ = read_pdf_text(
        pdf_bytes
    )

    assert len(reader.pages) >= 1


def test_pdf_contains_generated_brief_content():

    brief = load_brief()

    pdf_bytes = export_legal_brief_pdf(
        brief
    )

    _, text = read_pdf_text(
        pdf_bytes
    )

    assert brief.title in text

    assert brief.legal_analysis[0].claim_id in text


def test_pdf_contains_disclaimer():

    brief = load_brief()

    pdf_bytes = export_legal_brief_pdf(
        brief
    )

    _, text = read_pdf_text(
        pdf_bytes
    )

    assert "AI-assisted legal research draft" in text

    assert "independently verified" in text


def test_pdf_export_does_not_modify_brief():

    brief = load_brief()

    before = brief.model_dump(
        mode="json"
    )

    export_legal_brief_pdf(
        brief
    )

    after = brief.model_dump(
        mode="json"
    )

    assert before == after
