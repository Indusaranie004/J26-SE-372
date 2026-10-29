from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

# supported judicial treatment relationship types
TreatmentStatus = Literal [
    "followed",
    "distinguished",
    "overruled",
    "doubted",
    "criticized",
    "unknown"
]

# overall precedent validity, provided by upstream components
ValidityStatus = Literal [
    "good_law",
    "partially_invalidated",
    "no_longer_good_law",
    "unknown"
]

# a passage from a legal judgment
class Passage(BaseModel):
    passage_id: str = Field(min_length=1)
    text: str = Field(min_length=1)

    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

# legislation associated with a precedent
class Legislation(BaseModel):
    act_id: str | None = None
    name: str | None = None
    section: str | None = None
    text: str | None = None

# a directional judicial treatment relationship
class JudicialTreatment(BaseModel):
    source_case_id: str = Field(min_length=1)
    target_case_id: str = Field(min_length=1)
    status: TreatmentStatus

    effective_date: date | None = None
    scope: str | None = None
    evidence: str | None = None
    char_offset: int | None = Field(default=None, ge=0)

# overall validity information from A
class ValidityAssessment(BaseModel):
    status: ValidityStatus = "unknown"

    safe_to_cite: bool | None = None
    summary: str | None = None
    as_of: str | None = None

# litigation history across different court levels
class LitigationStep(BaseModel):
    """
    Litigation-history information associated
    with a precedent.

    Full court metadata may be supplied later.

    Component B PP1 currently returns only a
    related case ID and graph-hop distance,
    therefore missing information remains None.
    """

    court: str | None = None

    case_number: str | None = None

    place: str | None = None

    source: str | None = None

    related_case_id: str | None = None

    hops: int | None = Field(
        default=None,
        ge=1
    )

# one retrieved legal precedent
class Precedent(BaseModel):
    case_id: str = Field(min_length=1)

    case_name: str | None = None
    case_number: str | None = None
    court: str | None = None
    judgment_date: date | None = None

    # retrieval score may not always be normalized
    relevance_score: float | None = None

    passages: list[Passage] = Field(default_factory = list)
    legislation: list[Legislation] = Field(default_factory = list)

    judicial_treatments: list[JudicialTreatment] = Field(
        default_factory = list
    )

    validity: ValidityAssessment | None = None

    litigation_history: list[LitigationStep] = Field(
        default_factory = list
    )

# complete input to C's reasoning pipeline
class ReasoningRequest(BaseModel):
    query: str = Field(min_length=1)

    case_facts: list[str] = Field(default_factory=list)

    precedents: list[Precedent] = Field(min_length=1)

    reference_date: date | None = None
