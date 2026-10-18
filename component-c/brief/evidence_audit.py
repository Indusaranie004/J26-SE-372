
"""
Component C - Function 2
Claim-to-Evidence Audit

Builds a deterministic audit report showing:
1. Every generated legal claim
2. Its model-assigned support status
3. The original evidence cited by the claim
4. Whether each reference can be resolved
5. Potential citation issues for human review

IMPORTANT:
Reference resolution is NOT semantic verification.

This module does not contact Gemini, invent
legal facts, or modify the generated brief.
"""

import re

from pydantic import BaseModel, Field

from brief.input_models import BriefGenerationRequest
from brief.output_models import (
    BriefEvidenceReference,
    LegalBrief,
)
from brief.brief_formatter import (
    BRIEF_SECTIONS,
    format_evidence_reference,
)


class AuditCitation(BaseModel):
    """A generated citation and its source evidence."""

    source_type: str
    label: str
    found: bool
    source_text: str | None = None
    source_details: str | None = None


class AuditClaim(BaseModel):
    """One generated claim and its evidence audit."""

    section: str
    claim_id: str
    statement: str
    model_support_status: str

    citations: list[AuditCitation] = Field(
        default_factory=list
    )

    review_flags: list[str] = Field(
        default_factory=list
    )


class EvidenceAuditReport(BaseModel):
    """Complete claim-to-evidence audit."""

    document_title: str
    source_question: str

    claims: list[AuditClaim] = Field(
        default_factory=list
    )

    @property
    def total_claims(self) -> int:
        return len(self.claims)

    @property
    def total_references(self) -> int:
        return sum(
            len(claim.citations)
            for claim in self.claims
        )

    @property
    def unresolved_references(self) -> int:
        return sum(
            not citation.found
            for claim in self.claims
            for citation in claim.citations
        )

    @property
    def flagged_claims(self) -> int:
        return sum(
            bool(claim.review_flags)
            for claim in self.claims
        )


def _normalize(value: str | None) -> str | None:
    """Normalize supplied identifiers for matching."""

    if value is None:
        return None

    return value.strip().casefold()


def _resolve_reference(
    reference: BriefEvidenceReference,
    request: BriefGenerationRequest,
) -> AuditCitation:
    """
    Find the original evidence cited by
    a generated BriefEvidenceReference.

    This lookup does not judge semantic support.
    """

    source = request.source_request

    label = format_evidence_reference(
        reference
    )

    def missing() -> AuditCitation:
        return AuditCitation(
            source_type=reference.source_type,
            label=label,
            found=False,
            source_details=(
                "The referenced record was not found "
                "in the supplied source evidence."
            ),
        )

    # -----------------------------------------
    # Judgment passage
    # -----------------------------------------

    if reference.source_type == "case_passage":

        for precedent in source.precedents:

            if precedent.case_id != reference.case_id:
                continue

            for passage in precedent.passages:

                if passage.passage_id == reference.passage_id:

                    return AuditCitation(
                        source_type="case_passage",
                        label=label,
                        found=True,
                        source_text=passage.text,
                        source_details=(
                            "Supplied judgment passage from "
                            f"{precedent.case_name or precedent.case_id}. "
                            "The original published judgment "
                            "has not been independently checked."
                        ),
                    )

        return missing()

    # -----------------------------------------
    # Original case fact
    # -----------------------------------------

    if reference.source_type == "case_fact":

        index = reference.fact_index

        if index is not None and (
            0 <= index < len(source.case_facts)
        ):

            return AuditCitation(
                source_type="case_fact",
                label=label,
                found=True,
                source_text=source.case_facts[index],
                source_details=(
                    f"Original supplied case fact, index {index}."
                ),
            )

        return missing()

    # -----------------------------------------
    # Legislation
    # -----------------------------------------

    if reference.source_type == "legislation":

        for precedent in source.precedents:

            for law in precedent.legislation:

                if reference.act_id is not None:
                    if _normalize(law.act_id) != _normalize(
                        reference.act_id
                    ):
                        continue

                if reference.legislation_name is not None:
                    if _normalize(law.name) != _normalize(
                        reference.legislation_name
                    ):
                        continue

                if reference.section is not None:
                    if _normalize(law.section) != _normalize(
                        reference.section
                    ):
                        continue

                return AuditCitation(
                    source_type="legislation",
                    label=label,
                    found=True,
                    source_text=law.text or None,
                    source_details=(
                        "Supplied legislation record attached "
                        f"to precedent {precedent.case_id}. "
                        "The full Act and surrounding provisions "
                        "have not been independently checked."
                    ),
                )

        return missing()

    # -----------------------------------------
    # Judicial-treatment metadata
    # -----------------------------------------

    if reference.source_type == "judicial_treatment":

        for precedent in source.precedents:

            if precedent.case_id != reference.target_case_id:
                continue

            for treatment in precedent.judicial_treatments:

                if (
                    treatment.source_case_id
                    != reference.source_case_id
                ):
                    continue

                if (
                    treatment.target_case_id
                    != reference.target_case_id
                ):
                    continue

                if (
                    treatment.status
                    != reference.treatment_status
                ):
                    continue

                if reference.effective_date is not None:
                    if (
                        treatment.effective_date
                        != reference.effective_date
                    ):
                        continue

                if reference.scope is not None:
                    if (
                        _normalize(treatment.scope)
                        != _normalize(reference.scope)
                    ):
                        continue

                details = [
                    "Supplied directional judicial-treatment metadata.",
                    (
                        "Relationship: "
                        f"{treatment.source_case_id} "
                        f"--{treatment.status}--> "
                        f"{treatment.target_case_id}."
                    ),
                ]

                if treatment.effective_date:
                    details.append(
                        "Effective date: "
                        + treatment.effective_date.isoformat()
                    )

                if treatment.scope:
                    details.append(
                        "Scope: " + treatment.scope
                    )

                details.append(
                    "The treating judgment has not been "
                    "independently verified."
                )

                return AuditCitation(
                    source_type="judicial_treatment",
                    label=label,
                    found=True,
                    source_text=treatment.evidence or None,
                    source_details=" ".join(details),
                )

        return missing()

    return missing()


def _mentions_judicial_treatment(
    statement: str,
) -> bool:
    """
    Identify treatment-related wording for
    additional manual review.

    This is a heuristic, not a semantic
    legal interpretation.
    """

    return bool(
        re.search(
            r"\b(overruled|distinguished|followed by|"
            r"criticized|doubted)\b",
            statement,
            flags=re.IGNORECASE,
        )
    )


def create_evidence_audit(
    request: BriefGenerationRequest,
    brief: LegalBrief,
) -> EvidenceAuditReport:
    """
    Build an audit from the original evidence
    and an already generated legal brief.

    This does not modify the brief.
    """

    if brief.title != request.title:
        raise ValueError(
            "Brief title does not match its source request."
        )

    audit_claims = []

    for _, section_name in BRIEF_SECTIONS:

        claims = getattr(brief, section_name)

        for claim in claims:

            citations = [
                _resolve_reference(reference, request)
                for reference in claim.evidence_references
            ]

            review_flags = []

            if any(
                not citation.found
                for citation in citations
            ):
                review_flags.append(
                    "One or more evidence references "
                    "could not be resolved."
                )

            # Detect treatment-related claims that
            # cite passages but no treatment metadata.
            mentions_treatment = (
                section_name == "precedent_treatment"
                or _mentions_judicial_treatment(
                    claim.statement
                )
            )

            has_treatment_reference = any(
                citation.source_type == "judicial_treatment"
                for citation in citations
            )

            if (
                mentions_treatment
                and not has_treatment_reference
            ):
                review_flags.append(
                    "This statement discusses judicial "
                    "treatment but cites no judicial-treatment "
                    "metadata. Review the source relationship."
                )

            # Surface records where legislative wording
            # is not actually available for comparison.
            if any(
                citation.source_type == "legislation"
                and citation.found
                and not citation.source_text
                for citation in citations
            ):
                review_flags.append(
                    "A cited legislation record contains "
                    "no supplied statutory text."
                )

            audit_claims.append(
                AuditClaim(
                    section=section_name,
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    model_support_status=claim.support_status,
                    citations=citations,
                    review_flags=review_flags,
                )
            )

    return EvidenceAuditReport(
        document_title=brief.title,
        source_question=request.source_request.query,
        claims=audit_claims,
    )


def _as_blockquote(text: str) -> str:
    """Format exact supplied evidence as Markdown."""

    return "\n".join(
        "> " + line
        for line in text.splitlines()
    )


def format_evidence_audit(
    audit: EvidenceAuditReport,
) -> str:
    """
    Format an evidence audit as readable Markdown.

    Every claim is displayed with its original
    cited source text where available.
    """

    lines = [
        f"# Evidence Audit: {audit.document_title}",
        "",
        "**Audit type:** Claim-to-source reference review",
        "",
        "**Source question:** " + audit.source_question,
        "",
        (
            "**Important:** The support statuses below "
            "were assigned by the generating language "
            "model. This audit resolves supplied source "
            "references but does NOT establish semantic "
            "entailment or independent legal correctness."
        ),
        "",
        "## Audit Summary",
        "",
        f"- Claims reviewed: {audit.total_claims}",
        f"- Evidence references: {audit.total_references}",
        (
            "- Unresolved references: "
            f"{audit.unresolved_references}"
        ),
        f"- Claims with review flags: {audit.flagged_claims}",
        "",
        "---",
        "",
    ]

    current_section = None

    for claim in audit.claims:

        if claim.section != current_section:

            current_section = claim.section

            heading = current_section.replace(
                "_", " "
            ).title()

            lines.extend([
                f"## {heading}",
                "",
            ])

        lines.extend([
            f"### {claim.claim_id}",
            "",
            (
                "**Model-assigned support status:** "
                + claim.model_support_status.replace("_", " ")
            ),
            "",
            "**Generated statement:**",
            "",
            claim.statement,
            "",
        ])

        if not claim.citations:

            lines.extend([
                "**Cited evidence:** None",
                "",
            ])

        for index, citation in enumerate(
            claim.citations,
            start=1,
        ):

            resolution = (
                "Found in supplied evidence"
                if citation.found
                else "NOT FOUND"
            )

            lines.extend([
                (
                    f"**Evidence reference {index}:** "
                    f"{citation.label}"
                ),
                "",
                f"**Reference resolution:** {resolution}",
                "",
            ])

            if citation.source_text:

                lines.extend([
                    "**Original supplied evidence text:**",
                    "",
                    _as_blockquote(citation.source_text),
                    "",
                ])

            else:

                lines.extend([
                    (
                        "**Original supplied evidence text:** "
                        "Not available for this reference."
                    ),
                    "",
                ])

            if citation.source_details:

                lines.extend([
                    (
                        "**Source information:** "
                        + citation.source_details
                    ),
                    "",
                ])

        if claim.review_flags:

            lines.extend([
                "**Review flags:**",
                "",
            ])

            for flag in claim.review_flags:
                lines.append(f"- {flag}")

            lines.append("")

        lines.extend([
            "**Human assessment:** Not yet evaluated",
            "",
            "---",
            "",
        ])

    lines.extend([
        "## Evaluation Guidance",
        "",
        (
            "A legal reviewer should compare each "
            "generated statement against the exact "
            "supplied source text, verify treatment "
            "relationships and scope, and identify "
            "unsupported or overstated propositions."
        ),
        "",
        (
            "A resolved citation confirms only that "
            "the referenced input record exists. "
            "It does not prove that the record "
            "supports the generated statement."
        ),
        "",
        (
            "**Research status:** Fictional development "
            "experiment. Not a court-ready legal document."
        ),
        "",
    ])

    return "\n".join(lines)
