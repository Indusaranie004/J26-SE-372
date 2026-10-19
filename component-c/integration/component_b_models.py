"""
Component B -> Component C integration models.

These models represent the current PP1 cluster payload supplied
by Component B.

Passage-level retrieval is intentionally not part of this
contract yet. Component C therefore continues using the graph
metadata currently supplied by Component B.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from reasoning.input_models import TreatmentStatus


class ComponentBCaseRelation(BaseModel):
    """
    A citation relationship attached to a seed precedent.
    """

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(min_length=1)

    citation_type: TreatmentStatus

    evidence: str | None = None

    scope: str | None = None


class ComponentBLegislation(BaseModel):
    """
    Legislation linked to a Component B seed precedent.
    """

    model_config = ConfigDict(extra="forbid")

    act_id: str | None = None

    name: str | None = None

    section: str | None = None


class ComponentBAppealChainItem(BaseModel):
    """
    Sparse appeal-chain relationship currently returned
    by Component B.

    Component B currently provides the related case ID
    and graph distance only.
    """

    model_config = ConfigDict(extra="forbid")

    related_id: str = Field(min_length=1)

    hops: int = Field(ge=1)


class ComponentBCluster(BaseModel):
    """
    One graph-expanded precedent cluster returned
    by Component B.
    """

    model_config = ConfigDict(extra="forbid")

    seed_id: str = Field(min_length=1)

    rrf_score: float | None = None

    cases_cited: list[ComponentBCaseRelation] = Field(
        default_factory=list
    )

    cited_by: list[ComponentBCaseRelation] = Field(
        default_factory=list
    )

    legislation: list[ComponentBLegislation] = Field(
        default_factory=list
    )

    appeal_chain: list[ComponentBAppealChainItem] = Field(
        default_factory=list
    )


class ComponentBReasoningRequest(BaseModel):
    """
    Input accepted at the Component B -> C boundary.

    query, case_facts and reference_date belong to
    the user's legal reasoning request.

    clusters contains the current output of
    Component B's PP1 retrieval stage.
    """

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)

    case_facts: list[str] = Field(
        default_factory=list
    )

    reference_date: date | None = None

    clusters: list[ComponentBCluster] = Field(
        min_length=1
    )