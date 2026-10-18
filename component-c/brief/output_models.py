
"""
Component C - Function 2
Evidence-Grounded Legal Brief Output Models

Defines:
1. Evidence references
2. Legal claims
3. Structured legal brief sections
4. Basic structural validation

Supported evidence types:
- Judgment passage
- Legislation
- Original case fact
- Judicial-treatment metadata

These models validate structure, not the
semantic correctness of legal conclusions.
"""

from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from reasoning.input_models import TreatmentStatus


class BriefEvidenceReference(BaseModel):
    """
    Identifies supplied evidence referenced by
    a claim in a generated legal brief.
    """

    model_config = ConfigDict(extra="forbid")

    source_type: Literal[
        "case_passage",
        "legislation",
        "case_fact",
        "judicial_treatment",
    ]

    # Judgment passage references
    case_id: str | None = None
    passage_id: str | None = None

    # Legislation references
    act_id: str | None = None
    legislation_name: str | None = None
    section: str | None = None

    # Original case fact references
    fact_index: int | None = Field(
        default=None,
        ge=0
    )

    # Judicial-treatment metadata references
    source_case_id: str | None = None
    target_case_id: str | None = None
    treatment_status: TreatmentStatus | None = None
    effective_date: date | None = None
    scope: str | None = None

    @model_validator(mode="after")
    def validate_reference(self):
        """
        Check required identifiers for the
        selected evidence reference type.
        """

        if self.source_type == "case_passage":

            if not self.case_id or not self.passage_id:
                raise ValueError(
                    "A case passage reference requires "
                    "case_id and passage_id."
                )

        elif self.source_type == "legislation":

            if not self.act_id and not self.legislation_name:
                raise ValueError(
                    "A legislation reference requires "
                    "act_id or legislation_name."
                )

        elif self.source_type == "case_fact":

            if self.fact_index is None:
                raise ValueError(
                    "A case fact reference requires "
                    "fact_index."
                )

        elif self.source_type == "judicial_treatment":

            if (
                not self.source_case_id
                or not self.target_case_id
                or not self.treatment_status
            ):
                raise ValueError(
                    "A judicial-treatment reference requires "
                    "source_case_id, target_case_id "
                    "and treatment_status."
                )

        return self


class BriefClaim(BaseModel):
    """
    Represents an individual statement in
    the generated legal research brief.
    """

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)

    statement: str = Field(min_length=1)

    support_status: Literal[
        "supported",
        "contested",
        "insufficient_evidence",
    ]

    evidence_references: list[
        BriefEvidenceReference
    ] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_claim_support(self):
        """
        Supported and contested claims must
        contain at least one evidence reference.
        """

        if self.support_status in {
            "supported",
            "contested",
        } and not self.evidence_references:

            raise ValueError(
                "Supported and contested claims "
                "must include evidence references."
            )

        return self


class LegalBrief(BaseModel):
    """
    Structured evidence-grounded legal research brief.

    This is a research draft, not a
    court-ready legal filing.
    """

    model_config = ConfigDict(extra="forbid")

    document_type: Literal[
        "research_brief"
    ] = "research_brief"

    title: str = Field(min_length=1)

    legal_issue: str = Field(min_length=1)

    relevant_facts: list[BriefClaim] = Field(
        default_factory=list
    )

    applicable_legislation: list[BriefClaim] = Field(
        default_factory=list
    )

    relevant_precedents: list[BriefClaim] = Field(
        default_factory=list
    )

    precedent_treatment: list[BriefClaim] = Field(
        default_factory=list
    )

    legal_analysis: list[BriefClaim] = Field(
        min_length=1
    )

    arguments: list[BriefClaim] = Field(
        default_factory=list
    )

    counterarguments: list[BriefClaim] = Field(
        default_factory=list
    )

    application_to_facts: list[BriefClaim] = Field(
        default_factory=list
    )

    conclusion: list[BriefClaim] = Field(
        min_length=1
    )

    limitations: list[str] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validate_unique_claim_ids(self):
        """
        Ensure claim IDs are unique throughout
        all sections of the legal brief.
        """

        sections = [
            self.relevant_facts,
            self.applicable_legislation,
            self.relevant_precedents,
            self.precedent_treatment,
            self.legal_analysis,
            self.arguments,
            self.counterarguments,
            self.application_to_facts,
            self.conclusion,
        ]

        seen_ids = set()

        for section in sections:
            for claim in section:

                if claim.claim_id in seen_ids:
                    raise ValueError(
                        "Duplicate claim ID: "
                        + claim.claim_id
                    )

                seen_ids.add(claim.claim_id)

        return self
