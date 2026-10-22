
"""
Structured Legal Reasoning Output Models
Component C - Function 1

Defines the validated output of cross-case
contextual and precedent-aware legal reasoning.

Includes structured comparison of court hierarchy,
chronology, judicial treatment, and conflicts.
"""

from pydantic import BaseModel, ConfigDict, Field

from reasoning.input_models import ValidityStatus


class EvidenceReference(BaseModel):
    """
    References an existing judgment passage
    from the supplied legal evidence.
    """

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    passage_id: str = Field(min_length=1)


class AuthorityAnalysis(BaseModel):
    """
    Structured analysis of one supplied precedent.
    """

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)

    case_name: str | None = None
    court: str | None = None

    relevance_to_issue: str = Field(min_length=1)

    validity_status: ValidityStatus = "unknown"

    judicial_treatment_summary: str = Field(
        min_length=1
    )

    authority_assessment: str = Field(
        min_length=1
    )

    supporting_evidence: list[EvidenceReference] = Field(
        default_factory=list
    )


class AuthorityComparison(BaseModel):
    """
    Structured comparison across supplied precedents.

    These fields contain auditable summaries
    of the legal considerations, not private
    chain-of-thought.

    None means the consideration has not
    been separately evaluated or supplied.
    """

    model_config = ConfigDict(extra="forbid")

    hierarchy_considerations: str | None = Field(
        default=None,
        min_length=1
    )

    chronology_considerations: str | None = Field(
        default=None,
        min_length=1
    )

    judicial_treatment_considerations: str | None = Field(
        default=None,
        min_length=1
    )

    conflicts_or_distinctions: str | None = Field(
        default=None,
        min_length=1
    )


class ReasoningResponse(BaseModel):
    """
    Complete structured cross-case legal reasoning.

    Preserves the original Day 1 fields and
    introduces structured authority comparison.
    """

    model_config = ConfigDict(extra="forbid")

    legal_issue: str = Field(min_length=1)

    relevant_facts: list[str] = Field(
        default_factory=list
    )

    authorities: list[AuthorityAnalysis] = Field(
        min_length=1
    )

    # New: separate comparative legal considerations
    authority_comparison: AuthorityComparison = Field(
        default_factory=AuthorityComparison
    )

    # Existing consolidated legal synthesis
    cross_case_analysis: str = Field(
        min_length=1
    )

    legislation_considered: list[str] = Field(
        default_factory=list
    )

    application: str = Field(min_length=1)

    conclusion: str = Field(min_length=1)

    limitations_or_insufficient_evidence: list[str] = Field(
        default_factory=list
    )
