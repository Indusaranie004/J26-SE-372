"""
Component B -> Component C Adapter

Normalizes Component B's current PP1 cluster response
into the ReasoningRequest already consumed by
Component C Function 1.

Important boundaries:

- No passage text is invented when passage retrieval
  is absent.

- No case metadata, validity status or treatment date
  is invented.

- Citation direction is preserved explicitly.

- Sparse appeal-chain data is retained only as
  related-case/hop metadata.

- Missing court-level details remain missing.
"""

from integration.component_b_models import (
    ComponentBCaseRelation,
    ComponentBCluster,
    ComponentBReasoningRequest,
)

from reasoning.input_models import (
    JudicialTreatment,
    Legislation,
    LitigationStep,
    Precedent,
    ReasoningRequest,
)


def _map_legislation(
    cluster: ComponentBCluster
) -> list[Legislation]:
    """
    Convert Component B legislation records.

    Statutory text is not currently supplied by B,
    therefore it remains None.
    """

    return [
        Legislation(
            act_id=item.act_id,
            name=item.name,
            section=item.section,
            text=None,
        )
        for item in cluster.legislation
    ]


def _outgoing_treatment(
    seed_id: str,
    relation: ComponentBCaseRelation,
) -> JudicialTreatment:
    """
    Convert a Component B cases_cited relationship.

    Direction:

        seed_id --citation_type--> target_id

    The seed judgment is the judgment performing
    the treatment.
    """

    return JudicialTreatment(
        source_case_id=seed_id,
        target_case_id=relation.target_id,
        status=relation.citation_type,

        # B does not currently provide these.
        effective_date=None,
        char_offset=None,

        # Preserve the supplied B values.
        scope=relation.scope,
        evidence=relation.evidence,
    )


def _incoming_treatment(
    seed_id: str,
    relation: ComponentBCaseRelation,
) -> JudicialTreatment:
    """
    Convert a Component B cited_by relationship.

    For cited_by, the related case is the source
    judgment and the seed case is the target:

        related case --citation_type--> seed case

    Component B currently calls the related ID
    `target_id` even inside cited_by. This adapter
    resolves the direction here.
    """

    return JudicialTreatment(
        source_case_id=relation.target_id,
        target_case_id=seed_id,
        status=relation.citation_type,

        effective_date=None,
        scope=relation.scope,
        evidence=relation.evidence,
        char_offset=None,
    )


def _map_treatments(
    cluster: ComponentBCluster,
) -> list[JudicialTreatment]:
    """
    Convert outgoing and incoming
    judicial-treatment relationships.
    """

    treatments = [
        _outgoing_treatment(
            cluster.seed_id,
            relation
        )
        for relation in cluster.cases_cited
    ]

    treatments.extend(
        _incoming_treatment(
            cluster.seed_id,
            relation
        )
        for relation in cluster.cited_by
    )

    return treatments


def _map_appeal_chain(
    cluster: ComponentBCluster,
) -> list[LitigationStep]:
    """
    Preserve the appeal-chain information B
    currently supplies.

    Component C does not invent a court,
    case number or appeal direction.
    """

    return [
        LitigationStep(
            related_case_id=item.related_id,
            hops=item.hops,
            source="Component B appeal_chain",
        )
        for item in cluster.appeal_chain
    ]


def _map_cluster(
    cluster: ComponentBCluster
) -> Precedent:
    """
    Convert one Component B cluster into
    Component C's internal Precedent model.
    """

    return Precedent(
        case_id=cluster.seed_id,

        # RRF is retrieval relevance metadata.
        relevance_score=cluster.rrf_score,

        # Passage retrieval is not implemented
        # by Component B at PP1.
        passages=[],

        legislation=_map_legislation(
            cluster
        ),

        judicial_treatments=_map_treatments(
            cluster
        ),

        # Do not invent validity information.
        validity=None,

        litigation_history=_map_appeal_chain(
            cluster
        ),
    )


def component_b_to_reasoning_request(
    payload: ComponentBReasoningRequest | dict,
) -> ReasoningRequest:
    """
    Normalize Component B PP1 output for
    Component C Function 1.

    Args:
        payload:
            A validated ComponentBReasoningRequest
            or a raw dictionary.

    Returns:
        ReasoningRequest accepted by the existing
        Component C reasoning pipeline.

    Raises:
        ValidationError:
            If B's input no longer follows the
            agreed interface.

        ValueError:
            If duplicate seed cases are supplied.
    """

    if isinstance(payload, dict):

        payload = (
            ComponentBReasoningRequest.model_validate(
                payload
            )
        )

    seed_ids = [
        cluster.seed_id
        for cluster in payload.clusters
    ]

    # A precedent should not appear as two
    # independent seed clusters in one request.
    if len(seed_ids) != len(set(seed_ids)):

        raise ValueError(
            "Component B payload contains "
            "duplicate seed_id values."
        )

    precedents = [
        _map_cluster(cluster)
        for cluster in payload.clusters
    ]

    return ReasoningRequest(
        query=payload.query,
        case_facts=payload.case_facts,
        reference_date=payload.reference_date,
        precedents=precedents,
    )