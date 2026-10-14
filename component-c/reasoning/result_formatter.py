
"""
Component C - Human-Readable Reasoning Formatter

Converts an existing structured ReasoningResponse
into a readable plain-text analysis report.

Important:
- Does not call an LLM.
- Does not perform new legal reasoning.
- Does not modify the original response.
- Does not verify legal correctness.
"""

from reasoning.output_models import ReasoningResponse


NOT_AVAILABLE = "Not available in this response."


def display_text(value: str | None) -> str:
    """Display optional text safely."""

    if value is None or not value.strip():
        return NOT_AVAILABLE

    return value


def format_reasoning_report(
    response: ReasoningResponse
) -> str:
    """
    Format a structured reasoning response
    as a readable plain-text report.
    """

    lines = [
        "COMPONENT C - LEGAL REASONING ANALYSIS",
        "=" * 45,
        (
            "Display-only formatting of an existing "
            "reasoning response."
        ),
        (
            "This report is not an independent "
            "verification of legal correctness."
        ),
    ]

    def add_section(title: str):
        """Add a consistently formatted section."""

        lines.append("")
        lines.append(title)
        lines.append("-" * len(title))

    # --------------------------------------------
    # 1. Legal issue
    # --------------------------------------------

    add_section("LEGAL ISSUE")
    lines.append(response.legal_issue)

    # --------------------------------------------
    # 2. Relevant facts
    # --------------------------------------------

    add_section("RELEVANT FACTS")

    if response.relevant_facts:
        for fact in response.relevant_facts:
            lines.append(f"- {fact}")
    else:
        lines.append("No relevant facts supplied.")

    # --------------------------------------------
    # 3. Authorities
    # --------------------------------------------

    add_section("AUTHORITIES CONSIDERED")

    for index, authority in enumerate(
        response.authorities,
        start=1
    ):
        lines.append("")
        lines.append(
            f"{index}. {authority.case_id}"
        )

        lines.append(
            f"   Case: "
            f"{display_text(authority.case_name)}"
        )

        lines.append(
            f"   Court: "
            f"{display_text(authority.court)}"
        )

        lines.append(
            f"   Validity: "
            f"{authority.validity_status}"
        )

        lines.append(
            "   Relevance: "
            + authority.relevance_to_issue
        )

        lines.append(
            "   Judicial Treatment: "
            + authority.judicial_treatment_summary
        )

        lines.append(
            "   Authority Assessment: "
            + authority.authority_assessment
        )

        # Preserve source passage references
        if authority.supporting_evidence:
            references = ", ".join(
                f"{reference.case_id}:"
                f"{reference.passage_id}"
                for reference
                in authority.supporting_evidence
            )

            lines.append(
                f"   Supporting Evidence: {references}"
            )
        else:
            lines.append(
                "   Supporting Evidence: "
                "No passage references supplied."
            )

    # --------------------------------------------
    # 4. Structured authority comparison
    # --------------------------------------------

    add_section("AUTHORITY COMPARISON")

    comparison = response.authority_comparison

    comparison_fields = [
        (
            "Court Hierarchy",
            comparison.hierarchy_considerations
        ),
        (
            "Chronology",
            comparison.chronology_considerations
        ),
        (
            "Judicial Treatment",
            comparison.judicial_treatment_considerations
        ),
        (
            "Conflicts or Distinctions",
            comparison.conflicts_or_distinctions
        ),
    ]

    for label, value in comparison_fields:
        lines.append("")
        lines.append(f"{label}:")
        lines.append(display_text(value))

    # --------------------------------------------
    # 5. Cross-case analysis
    # --------------------------------------------

    add_section("CROSS-CASE ANALYSIS")

    lines.append(response.cross_case_analysis)

    # --------------------------------------------
    # 6. Legislation
    # --------------------------------------------

    add_section("LEGISLATION CONSIDERED")

    if response.legislation_considered:
        for legislation in response.legislation_considered:
            lines.append(f"- {legislation}")
    else:
        lines.append("No legislation listed.")

    # --------------------------------------------
    # 7. Application
    # --------------------------------------------

    add_section("APPLICATION TO FACTS")

    lines.append(response.application)

    # --------------------------------------------
    # 8. Conclusion
    # --------------------------------------------

    add_section("CONCLUSION")

    lines.append(response.conclusion)

    # --------------------------------------------
    # 9. Limitations
    # --------------------------------------------

    add_section("LIMITATIONS / INSUFFICIENT EVIDENCE")

    if response.limitations_or_insufficient_evidence:
        for limitation in (
            response.limitations_or_insufficient_evidence
        ):
            lines.append(f"- {limitation}")
    else:
        lines.append("No limitations listed in response.")

    return "\n".join(lines)
