
"""
Component C - Function 2
Legal Brief Grounding Validator

Validates claim references against original evidence.

Checks:
1. Case IDs and passage IDs
2. Legislation references
3. Original case fact indices
4. Judicial-treatment relationships
5. Judicial-treatment dates and scopes where cited

Important:
This validator checks referential consistency.

It does not independently verify whether a
passage semantically supports a legal claim
or whether upstream legal metadata is correct.
"""

from brief.input_models import BriefGenerationRequest
from brief.output_models import (
    BriefEvidenceReference,
    LegalBrief,
)


BRIEF_CLAIM_SECTIONS = [
    "relevant_facts",
    "applicable_legislation",
    "relevant_precedents",
    "precedent_treatment",
    "legal_analysis",
    "arguments",
    "counterarguments",
    "application_to_facts",
    "conclusion",
]


def _normalize(value: str | None) -> str | None:
    """Normalize text identifiers for comparison."""

    if value is None:
        return None

    return value.strip().casefold()


def _legislation_exists(
    reference: BriefEvidenceReference,
    request: BriefGenerationRequest
) -> bool:
    """
    Verify that the legislation reference matches
    a supplied record.

    All provided identifiers must match
    the same legislation record.
    """

    for precedent in request.source_request.precedents:

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

            return True

    return False



def _judicial_treatment_exists(
    reference: BriefEvidenceReference,
    request: BriefGenerationRequest
) -> bool:
    """
    Verify a judicial-treatment relationship.

    Supports treatment metadata stored under
    either the source precedent or the target
    precedent.

    This is necessary because Component B
    supplies both cases_cited and cited_by
    relationships.

    Relationship direction remains:

    source_case_id --status--> target_case_id
    """

    for precedent in request.source_request.precedents:

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

            return True

    return False



def validate_brief_grounding(
    request: BriefGenerationRequest,
    brief: LegalBrief
) -> list[str]:
    """
    Validate generated claim references against
    the original source evidence.

    Returns an empty list if all referenced
    identifiers and relationships are found.

    Does not guarantee semantic correctness.
    """

    errors = []

    # Build a case-to-passage lookup.
    case_passages = {}

    for precedent in request.source_request.precedents:

        case_passages[precedent.case_id] = {
            passage.passage_id
            for passage in precedent.passages
        }

    fact_count = len(
        request.source_request.case_facts
    )

    # Check every section containing legal claims.
    for section_name in BRIEF_CLAIM_SECTIONS:

        claims = getattr(brief, section_name)

        for claim in claims:

            claim_location = (
                f"{section_name}/{claim.claim_id}"
            )

            for reference in claim.evidence_references:

                # -----------------------------
                # Case passage reference
                # -----------------------------

                if reference.source_type == "case_passage":

                    if reference.case_id not in case_passages:

                        errors.append(
                            f"{claim_location}: "
                            f"Unknown case ID "
                            f"'{reference.case_id}'."
                        )

                        continue

                    available_passages = case_passages[
                        reference.case_id
                    ]

                    if (
                        reference.passage_id
                        not in available_passages
                    ):

                        errors.append(
                            f"{claim_location}: "
                            f"Passage ID '{reference.passage_id}' "
                            f"was not supplied for case "
                            f"'{reference.case_id}'."
                        )

                # -----------------------------
                # Legislation reference
                # -----------------------------

                elif reference.source_type == "legislation":

                    if not _legislation_exists(
                        reference,
                        request
                    ):

                        errors.append(
                            f"{claim_location}: "
                            "Legislation reference does not "
                            "match the supplied evidence."
                        )

                # -----------------------------
                # Case fact reference
                # -----------------------------

                elif reference.source_type == "case_fact":

                    if (
                        reference.fact_index is None
                        or reference.fact_index >= fact_count
                    ):

                        errors.append(
                            f"{claim_location}: "
                            f"Invalid fact index "
                            f"'{reference.fact_index}'. "
                            f"Available fact count: "
                            f"{fact_count}."
                        )

                # -----------------------------
                # Judicial-treatment reference
                # -----------------------------

                elif reference.source_type == "judicial_treatment":

                    if not _judicial_treatment_exists(
                        reference,
                        request
                    ):

                        errors.append(
                            f"{claim_location}: "
                            "Judicial-treatment reference "
                            "does not match the supplied "
                            "metadata."
                        )

    return errors
