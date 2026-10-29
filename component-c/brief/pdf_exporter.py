"""
Component C - Function 2
Professional PDF Legal Brief Exporter

Converts an existing LegalBrief into a
professionally formatted PDF document.

No Gemini API calls or new legal claims.
"""

import re

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm

from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from brief.output_models import LegalBrief

from brief.brief_formatter import (
    format_legal_brief,
)


# ---------------------------------------------
# PDF theme
# ---------------------------------------------

NAVY = colors.HexColor("#1D3146")
TEAL = colors.HexColor("#176870")
SLATE = colors.HexColor("#556370")

PALE = colors.HexColor("#EDF3F5")
BORDER = colors.HexColor("#CBD7DE")

DISCLAIMER = (
    "AI-assisted legal research draft. "
    "The cited authorities and legal conclusions "
    "must be independently verified before use."
)


# ---------------------------------------------
# Inline Markdown formatting
# ---------------------------------------------

def _inline(text):
    """
    Convert supported inline Markdown into
    safe ReportLab paragraph formatting.

    Supports:
    - Bold text
    - Inline code
    - Highlighted claim IDs
    """

    fragments = re.split(
        r"(\*\*.*?\*\*|`[^`]+`|CLAIM_\d+)",
        text,
    )

    rendered = []

    for item in fragments:

        if not item:
            continue

        # Bold
        if (
            item.startswith("**")
            and item.endswith("**")
        ):

            rendered.append(
                "<b>"
                + escape(item[2:-2])
                + "</b>"
            )

        # Inline code
        elif (
            item.startswith("`")
            and item.endswith("`")
        ):

            rendered.append(
                '<font color="#176870" face="Courier">'
                + escape(item[1:-1])
                + "</font>"
            )

        # Claim identifier
        elif re.fullmatch(
            r"CLAIM_\d+",
            item,
        ):

            rendered.append(
                '<font color="#176870"><b>'
                + item
                + "</b></font>"
            )

        # Ordinary text
        else:

            rendered.append(
                escape(item)
            )

    return "".join(rendered)


# ---------------------------------------------
# PDF typography and styles
# ---------------------------------------------

def _styles():
    """
    Create reusable paragraph styles.
    """

    sheet = getSampleStyleSheet()

    specifications = [
        (
            "LegalEyebrow",
            "Normal",
            "Helvetica-Bold",
            8.2,
            11,
            TEAL,
            0,
            5,
        ),
        (
            "LegalTitle",
            "Title",
            "Helvetica-Bold",
            18,
            23,
            NAVY,
            0,
            10,
        ),
        (
            "LegalH1",
            "Heading1",
            "Helvetica-Bold",
            12.5,
            16,
            TEAL,
            15,
            7,
        ),
        (
            "LegalH2",
            "Heading2",
            "Helvetica-Bold",
            11,
            14,
            NAVY,
            11,
            5,
        ),
        (
            "LegalH3",
            "Heading3",
            "Helvetica-Bold",
            10,
            13,
            NAVY,
            8,
            4,
        ),
        (
            "LegalBody",
            "Normal",
            "Helvetica",
            9.6,
            14.5,
            NAVY,
            0,
            7,
        ),
    ]

    for (
        name,
        parent,
        font,
        size,
        leading,
        color,
        before,
        after,
    ) in specifications:

        sheet.add(
            ParagraphStyle(
                name=name,
                parent=sheet[parent],
                fontName=font,
                fontSize=size,
                leading=leading,
                textColor=color,
                spaceBefore=before,
                spaceAfter=after,
                alignment=0,
                keepWithNext=(
                    name in {
                        "LegalH1",
                        "LegalH2",
                        "LegalH3",
                    }
                ),
            )
        )

    # -----------------------------------------
    # Bullet style
    # -----------------------------------------

    sheet.add(
        ParagraphStyle(
            name="LegalBullet",
            parent=sheet["LegalBody"],
            leftIndent=14,
            firstLineIndent=0,
            bulletIndent=3,
            spaceAfter=5,
        )
    )

    # -----------------------------------------
    # Quotation style
    # -----------------------------------------

    sheet.add(
        ParagraphStyle(
            name="LegalQuote",
            parent=sheet["LegalBody"],
            fontName="Helvetica-Oblique",
            textColor=SLATE,
            leftIndent=12,
        )
    )

    # -----------------------------------------
    # Disclaimer style
    # -----------------------------------------

    sheet.add(
        ParagraphStyle(
            name="LegalNotice",
            parent=sheet["LegalBody"],
            fontSize=8.8,
            leading=13,
            spaceAfter=0,
        )
    )

    return sheet


# ---------------------------------------------
# Convert Markdown lines
# ---------------------------------------------

def _add_line(
    story,
    raw_line,
    styles,
):
    """
    Add a Markdown line to the PDF story.
    """

    line = raw_line.strip()

    if not line:
        return

    # Horizontal separator
    if line in {
        "---",
        "***",
        "___",
    }:

        story.append(
            Spacer(1, 3 * mm)
        )

        return

    # Third-level heading
    if line.startswith("### "):

        story.append(
            Paragraph(
                _inline(line[4:]),
                styles["LegalH3"],
            )
        )

    # Second-level heading
    elif line.startswith("## "):

        story.append(
            Paragraph(
                _inline(line[3:]),
                styles["LegalH2"],
            )
        )

    # First-level heading
    elif line.startswith("# "):

        story.append(
            Paragraph(
                _inline(line[2:]),
                styles["LegalH1"],
            )
        )

        story.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=BORDER,
                spaceBefore=1,
                spaceAfter=6,
            )
        )

    # Bullet point
    elif (
        line.startswith("- ")
        or line.startswith("* ")
    ):

        story.append(
            Paragraph(
                _inline(line[2:]),
                styles["LegalBullet"],
                bulletText="-",
            )
        )

    # Quoted text
    elif line.startswith("> "):

        story.append(
            Paragraph(
                _inline(line[2:]),
                styles["LegalQuote"],
            )
        )

    # Ordinary text
    else:

        story.append(
            Paragraph(
                _inline(line),
                styles["LegalBody"],
            )
        )


# ---------------------------------------------
# Page header and footer
# ---------------------------------------------

def _header_footer(
    canvas,
    document,
):
    """
    Draw page headers and footers.
    """

    canvas.saveState()

    width, height = A4

    # Header separator
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)

    canvas.line(
        19 * mm,
        height - 15.5 * mm,
        width - 19 * mm,
        height - 15.5 * mm,
    )

    # Header label
    canvas.setFont(
        "Helvetica-Bold",
        7.5,
    )

    canvas.setFillColor(SLATE)

    canvas.drawRightString(
        width - 19 * mm,
        height - 12.6 * mm,
        "COMPONENT C  /  LEGAL RESEARCH",
    )

    # Footer separator
    canvas.line(
        19 * mm,
        16 * mm,
        width - 19 * mm,
        16 * mm,
    )

    # Footer text
    canvas.setFont(
        "Helvetica",
        7.5,
    )

    canvas.drawString(
        19 * mm,
        11.5 * mm,
        "AI-assisted legal research draft",
    )

    # Page number
    canvas.drawRightString(
        width - 19 * mm,
        11.5 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# ---------------------------------------------
# Main PDF exporter
# ---------------------------------------------

def export_legal_brief_pdf(
    brief: LegalBrief,
) -> bytes:
    """
    Generate a professionally formatted PDF.

    Returns:
        PDF document bytes.

    The original LegalBrief is not modified.
    """

    stream = BytesIO()

    # -----------------------------------------
    # Page configuration
    # -----------------------------------------

    document = SimpleDocTemplate(
        stream,
        pagesize=A4,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title=brief.title,
        author="Component C",
    )

    styles = _styles()

    # -----------------------------------------
    # Document heading
    # -----------------------------------------

    story = [
        Paragraph(
            "LEGAL RESEARCH BRIEF  /  REVIEW COPY",
            styles["LegalEyebrow"],
        ),
        Paragraph(
            escape(brief.title),
            styles["LegalTitle"],
        ),
        HRFlowable(
            width="100%",
            thickness=1.1,
            color=TEAL,
            spaceBefore=1,
            spaceAfter=12,
        ),
    ]

    # -----------------------------------------
    # Highlighted disclaimer
    # -----------------------------------------

    disclaimer = Table(
        [
            [
                Paragraph(
                    "<b>REVIEW REQUIRED</b>  |  "
                    + escape(DISCLAIMER),
                    styles["LegalNotice"],
                )
            ]
        ],
        colWidths=[
            A4[0] - 38 * mm
        ],
    )

    disclaimer.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    PALE,
                ),
                (
                    "LINEBEFORE",
                    (0, 0),
                    (0, -1),
                    2.4,
                    TEAL,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    11,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    11,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    story.extend(
        [
            disclaimer,
            Spacer(1, 6 * mm),
        ]
    )

    # -----------------------------------------
    # Generated legal brief content
    # -----------------------------------------

    markdown = format_legal_brief(
        brief
    )

    for raw_line in markdown.splitlines():

        line = raw_line.strip()

        # Avoid duplicating the document title
        if line in {
            f"# {brief.title}",
            f"## {brief.title}",
        }:
            continue

        _add_line(
            story,
            raw_line,
            styles,
        )

    # -----------------------------------------
    # Build PDF
    # -----------------------------------------

    document.build(
        story,
        onFirstPage=_header_footer,
        onLaterPages=_header_footer,
    )

    return stream.getvalue()