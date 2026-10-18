
"""
Component C - Function 2
Legal Brief Grounding Validator

Checks generated legal brief references against
the original evidence provided to Function 2.

Validates:
1. Supplied case identifiers
2. Passage ownership and existence
3. Supplied legislation identifiers and sections
4. Original case fact indices
5. Evidence references across all brief sections

Limitations:
This validator checks reference consistency.
It does not determine whether a passage
semantically supports a legal claim.
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
    """
    Normalize text identifiers for comparisons.

    For example:
    'Section 10' and 'section 10'
    will be treated as equivalent.

    This does not infer missing identifiers.
    """

    if value is None:
        return None

    return value.strip().casefold()


def _legislation_exists(
    reference: BriefEvidenceReference,
    request: BriefGenerationRequest
) -> bool:
    """
    Check whether a legislation reference matches
    a supplied legislation record.

    If the reference contains multiple identifiers,
    they must match the SAME legislation record.
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


def validate_brief_grounding(
    request: BriefGenerationRequest,
    brief: LegalBrief
) -> list[str]:
    """
    Validate all claim references against the
    original source evidence.

    Returns:
        A list of validation errors.

    An empty list means that all referenced
    identifiers were found in the source data.

    It does not guarantee semantic accuracy.
    """

    errors = []

    # -----------------------------------------
    # 1. Build original case-passage lookup
    # -----------------------------------------

    case_passages = {}

    for precedent in request.source_request.precedents:

        case_passages[precedent.case_id] = {
            passage.passage_id
            for passage in precedent.passages
        }

    # -----------------------------------------
    # 2. Determine valid fact indices
    # -----------------------------------------

    fact_count = len(
        request.source_request.case_facts
    )

    # -----------------------------------------
    # 3. Validate every brief section
    # -----------------------------------------

    for section_name in BRIEF_CLAIM_SECTIONS:

        claims = getattr(brief, section_name)

        for claim in claims:

            claim_location = (
                f"{section_name}/{claim.claim_id}"
            )

            # Each claim may have multiple references
            for reference in claim.evidence_references:

                # ---------------------------------
                # Case passage
                # ---------------------------------

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

                    if reference.passage_id not in available_passages:

                        errors.append(
                            f"{claim_location}: "
                            f"Passage ID '{reference.passage_id}' "
                            f"was not supplied for case "
                            f"'{reference.case_id}'."
                        )

                # ---------------------------------
                # Legislation
                # ---------------------------------

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

                # ---------------------------------
                # Case fact
                # ---------------------------------

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

    return errors
