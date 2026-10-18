
"""
Component C - Function 2
Evidence-Grounded Legal Brief Output Models

Defines:
1. Evidence references
2. Legal claims
3. Structured legal brief sections
4. Basic structural validation

These models validate structure, not the
semantic correctness of legal conclusions.
"""

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ---------------------------------------------
# Evidence reference
# ---------------------------------------------

class BriefEvidenceReference(BaseModel):
    """
    Identifies the supplied evidence supporting
    a statement in the generated legal brief.

    Supported reference types:
    - Judgment passage
    - Legislation
    - Original case fact
    """

    model_config = ConfigDict(extra="forbid")

    source_type: Literal[
        "case_passage",
        "legislation",
        "case_fact"
    ]

    case_id: str | None = None
    passage_id: str | None = None

    act_id: str | None = None
    legislation_name: str | None = None
    section: str | None = None

    fact_index: int | None = Field(
        default=None,
        ge=0
    )

    @model_validator(mode="after")
    def validate_reference(self):
        """
        Check the minimum identifiers required
        for each evidence reference type.
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

        return self


# ---------------------------------------------
# Evidence-grounded legal claim
# ---------------------------------------------

class BriefClaim(BaseModel):
    """
    Represents one important statement
    in the generated legal brief.

    Claims have explicit evidence references
    and an indication of evidentiary support.
    """

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)

    statement: str = Field(min_length=1)

    support_status: Literal[
        "supported",
        "contested",
        "insufficient_evidence"
    ]

    evidence_references: list[
        BriefEvidenceReference
    ] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_claim_support(self):
        """
        A claim marked supported or contested
        must identify at least one source.

        Whether that source genuinely supports
        the statement will be evaluated later.
        """

        if self.support_status in {
            "supported",
            "contested"
        } and not self.evidence_references:

            raise ValueError(
                "Supported and contested claims "
                "must include evidence references."
            )

        return self


# ---------------------------------------------
# Complete structured legal brief
# ---------------------------------------------

class LegalBrief(BaseModel):
    """
    Structured legal research brief.

    Substantive sections contain individual
    claims with traceable source references.

    The document is a research draft,
    not a court-ready legal filing.
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
        Ensure every claim in the document
        has a unique identifier.
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
