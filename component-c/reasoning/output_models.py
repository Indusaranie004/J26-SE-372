"""Structured output models for Component C

Defines the expected output of cross case contextual and precedent aware legal reasoning
"""

from pydantic import BaseModel, ConfigDict, Field

from reasoning.input_models import ValidityStatus

# References a passage from the supplied evidence
class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    passage_id: str = Field(min_length=1)

# Analysis of one retrieved precedent
class AuthorityAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    case_name: str | None = None
    court: str | None = None

    relevance_to_issue: str = Field(min_length=1)

    validity_status: ValidityStatus = "unknown"

    judicial_treatment_summary: str = Field(min_length=1)

    authority_assessment: str = Field(min_length=1)

    supporting_evidence: list[EvidenceReference] = Field(
        default_factory=list
    )


# Complete cross case legal reasoning output
class ReasoningResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal_issue: str = Field(min_length=1)

    relevant_facts: list[str] = Field(default_factory=list)

    authorities: list[AuthorityAnalysis] = Field(
        min_length=1
    )

    cross_case_analysis: str = Field(min_length=1)

    legislation_considered: list[str] = Field(
    default_factory=list
    )

    application: str = Field(min_length=1)

    conclusion: str = Field(min_length=1)

    limitations_or_insufficient_evidence: list[str] = Field(
    default_factory=list
    )