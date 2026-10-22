from typing import List

from config import NEO4J_USE_MOCK as USE_MOCK
from .models import (
    PrecedentCluster,
    LegalContext,
    CitationEdge,
    LegislationEdge,
    AppealEdge,
)

def _cites_outgoing(seed_id: str):
    if USE_MOCK:
        from data.mock_graph import mock_cites_outgoing
        return mock_cites_outgoing(seed_id)
    else:
        from .neo4j_client import neo4j_cites_outgoing
        return neo4j_cites_outgoing(seed_id)


def _cites_incoming(seed_id: str):
    if USE_MOCK:
        from data.mock_graph import mock_cites_incoming
        return mock_cites_incoming(seed_id)
    else:
        from .neo4j_client import neo4j_cites_incoming
        return neo4j_cites_incoming(seed_id)


def _legislation(seed_id: str):
    if USE_MOCK:
        from data.mock_graph import mock_legislation
        return mock_legislation(seed_id)
    else:
        from .neo4j_client import neo4j_legislation
        return neo4j_legislation(seed_id)


def _appeal_chain(seed_id: str):
    if USE_MOCK:
        from data.mock_graph import mock_appeal_chain
        return mock_appeal_chain(seed_id)
    else:
        from .neo4j_client import neo4j_appeal_chain
        return neo4j_appeal_chain(seed_id)


def expand(seed_ids: List[str]) -> List[PrecedentCluster]:
    """
    Graph expansion entry point.
    Takes a list of seed doc_ids as hybrid retrieval end-output.
    Returns one PrecedentCluster per seed, populated with:
      - judicial_treatment:     cases_cited (outgoing TREATED_BY *1..2)
                                cited_by (incoming TREATED_BY *1..1)
      - legislative_foundation: INVOLVES_ACT *1..1
      - litigation_history:     APPEALED_FROM *1..3 bidirectional

    """
    clusters = []

    for sid in seed_ids:
        clusters.append(PrecedentCluster(
            seed_id = sid,
            legal_context = LegalContext(

                judicial_treatment = [
                    CitationEdge(
                        target_id      = r["target"],
                        citation_type  = r["citation_type"],
                        direction      = "cases_cited",
                        evidence       = r.get("evidence"),
                        scope          = r.get("scope") or "full scope",
                        effective_date = r.get("effective_date"),
                    )
                    for r in _cites_outgoing(sid)
                ] + [
                    CitationEdge(
                        target_id      = r["source"],
                        citation_type  = r["citation_type"],
                        direction      = "cited_by",
                        evidence       = r.get("evidence"),
                        scope          = r.get("scope") or "full scope",
                        effective_date = r.get("effective_date"),
                    )
                    for r in _cites_incoming(sid)
                ],

                legislative_foundation = [
                    LegislationEdge(
                        act_id  = r["act_id"],
                        name    = r["name"],
                        section = r.get("section") or "Not specified in citation",
                    )
                    for r in _legislation(sid)
                ],

                litigation_history = [
                    AppealEdge(
                        related_id = r["related"],
                        hops       = r["hops"],
                        court      = r.get("court"),
                        judge      = r.get("judge"),
                    )
                    for r in _appeal_chain(sid)
                ],

            ),
        ))

    return clusters