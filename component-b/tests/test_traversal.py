import os
os.environ["NEO4J_USE_MOCK"] = "true"  # must be set BEFORE importing traversal

import pytest
from retrieval.expand.traversal import expand
from retrieval.expand.models import (
    PrecedentCluster,
    CitationEdge,
    LegislationEdge,
    AppealEdge,
)

SEED_A = "2016-07-22-SC-FR-527-2011"
SEED_B = "2017-02-15-SC-FR-394-2008"
SEED_C = "2017-03-03-SC-FR-164-2015"


def _c(sid):
    clusters = expand([sid])
    assert len(clusters) == 1
    return clusters[0]


#Returns a PrecedentCluster with the correct SeedID
def test_expand_returns_cluster():
    c = _c(SEED_A)
    assert isinstance(c, PrecedentCluster)
    assert c.seed_id == SEED_A


#Depth-1 outgoing citations work: SEED_A cites SEED_B and SEED_C directly
def test_cites_outgoing_depth1():
    ids = [e.target_id for e in _c(SEED_A).legal_context.judicial_treatment
           if e.direction == "cases_cited"]
    assert SEED_B in ids
    assert SEED_C in ids


#Depth-2 indirect citations work.
def test_cites_outgoing_depth2():
    """SEED_A -> SEED_B -> 2017-03-14-SC-APPEAL-167-2010 (FR-03: indirect citation)."""
    ids = [e.target_id for e in _c(SEED_A).legal_context.judicial_treatment
           if e.direction == "cases_cited"]
    assert "2017-03-14-SC-APPEAL-167-2010" in ids, "depth-2 indirect citation missing"


#Effective date is present on citation edges.
def test_citation_has_effective_date():
    """Confirmed field from A: TREATED_BY edge carries effective_date."""
    edges = [e for e in _c(SEED_A).legal_context.judicial_treatment
             if e.direction == "cases_cited"]
    assert len(edges) > 0
    assert edges[0].effective_date is not None


#Incoming citations work
def test_cited_by_depth1():
    ids = [e.target_id for e in _c(SEED_A).legal_context.judicial_treatment
           if e.direction == "cited_by"]
    assert "2017-01-20-SC-FR-57-2016" in ids

#Legislation links work
def test_legislation_links():
    leg = _c(SEED_A).legal_context.legislative_foundation
    assert len(leg) > 0
    assert isinstance(leg[0], LegislationEdge)
    act_ids = [l.act_id for l in leg]
    assert "act_cpc" in act_ids


#Every AppealEdge in litigation_history has hops ≥ 1 and a non-null court
def test_appeal_chain_has_court_and_judge():
    """AppealEdge must carry court property and optionally judge."""
    chain = _c(SEED_A).legal_context.litigation_history
    assert len(chain) > 0
    for e in chain:
        assert isinstance(e, AppealEdge)
        assert e.hops >= 1
        assert e.court is not None, "court property missing from AppealEdge"


#DC stub nodes with no judge are valid
def test_appeal_chain_judge_optional():
    """stub nodes (in_corpus=false) may have no judge — judge=None is valid."""
    chain = _c(SEED_A).legal_context.litigation_history
    courts = {e.court for e in chain}
    dc_edges = [e for e in chain if e.court == "DC"]
    assert all(e.judge is None for e in dc_edges)


#Unknown seed returns an empty cluster with no crashes.
def test_unknown_seed_returns_empty_cluster():
    c = _c("unknown-seed-xyz")
    assert c.legal_context.judicial_treatment    == []
    assert c.legal_context.legislative_foundation == []
    assert c.legal_context.litigation_history     == []


#Multiple seeds each get their own cluster; all three seed IDs are present in the result.
def test_multiple_seeds():
    clusters = expand([SEED_A, SEED_B, SEED_C])
    assert len(clusters) == 3
    assert {c.seed_id for c in clusters} == {SEED_A, SEED_B, SEED_C}