
"""
Evidence grounding validation for Component C

Checks whether the LLM output references actual
precedents and passages from the supplied input
"""

from collections import Counter

from reasoning.input_models import ReasoningRequest
from reasoning.output_models import ReasoningResponse


def validate_grounding(
    request: ReasoningRequest,
    response: ReasoningResponse
) -> list[str]:
    """
    Verify the generated reasoning against input metadata.

    Returns:
        List of detected problems.
        An empty list means all implemented checks passed.
    """

    errors = []

    # index the original precedents by ID
    precedent_map = {
        precedent.case_id: precedent
        for precedent in request.precedents
    }

    # track which precedents the LLM analyzed
    analyzed_ids = [
        authority.case_id
        for authority in response.authorities
    ]

    counts = Counter(analyzed_ids)

    for case_id in precedent_map:
        if counts[case_id] == 0:
            errors.append(
                f"Missing authority analysis: {case_id}"
            )
        elif counts[case_id] > 1:
            errors.append(
                f"Duplicate authority analysis: {case_id}"
            )

    # check each generated authority
    for authority in response.authorities:

        case_id = authority.case_id

        if case_id not in precedent_map:
            errors.append(
                f"Unknown authority: {case_id}"
            )
            continue

        original = precedent_map[case_id]

        # verify overall validity status
        expected_status = (
            original.validity.status
            if original.validity
            else "unknown"
        )

        if authority.validity_status != expected_status:
            errors.append(
                f"Validity mismatch for {case_id}: "
                f"expected {expected_status}, "
                f"got {authority.validity_status}"
            )

        # require passage references where passages exist
        if original.passages and not any(
            reference.case_id == case_id
            for reference in authority.supporting_evidence
        ):
            errors.append(
                f"No supporting passage from {case_id}"
            )

        # verify every cited case and passage
        for reference in authority.supporting_evidence:

            referenced_case = precedent_map.get(
                reference.case_id
            )

            if referenced_case is None:
                errors.append(
                    f"Unknown evidence case: "
                    f"{reference.case_id}"
                )
                continue

            valid_passage_ids = {
                passage.passage_id
                for passage in referenced_case.passages
            }

            if reference.passage_id not in valid_passage_ids:
                errors.append(
                    f"Unknown passage {reference.passage_id} "
                    f"in case {reference.case_id}"
                )

    return errors
