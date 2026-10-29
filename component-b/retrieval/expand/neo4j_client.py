import os
from neo4j import GraphDatabase

#Neo4J Integration Constants
NEO4J_URI      = os.getenv("NEO4J_URI", "")         
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

#Neo4j Schema Constants (Nodes and Edges)
CASE_LABEL   = "Case"          
ACT_LABEL    = "Act"           
JUDGE_LABEL  = "Judge"        
TREATED_BY   = "TREATED_BY"   
INVOLVES_ACT = "INVOLVES_ACT" 
DECIDED_BY   = "DECIDED_BY"   
APPEALED_FROM = "APPEALED_FROM" 

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    return _driver

#Edges having attributes. - Edges treated as DATA. (Triplet-Granular retrieval)
def neo4j_cites_outgoing(seed_id: str):

    #Captures the right hand side of the triplet (The edge + The target node) - Seed is the source node (left hand side of the triplet)

    """
    Outgoing TREATED_BY *1..2 (FR-03: indirect/chained citations required).
    Returns cases cited by the seed  with treatment type, evidence, effective date, scope.
    Field 'target' maps to CitationEdge.target_id in traversal.py.

    """
    
    q = """
        MATCH (s:Case {doc_id: $sid})
              -[r:TREATED_BY*1..2]->(t:Case)
        RETURN t.doc_id              AS target, 
               last(r).treatment_type AS citation_type,
               last(r).evidence       AS evidence,
               last(r).effective_date AS effective_date,
               last(r).scope          AS scope
    """
    with _get_driver().session() as session:
        return [dict(r) for r in session.run(q, sid=seed_id)]

#Edges having attributes. - Edges treated as DATA. (Triplet-Granular retrieval)
def neo4j_cites_incoming(seed_id: str):

    #Captures the right hand side of the triplet (The edge + The source node) - Seed is the target node (right hand side of the triplet)

    """
    Incoming TREATED_BY *1..1.
    Returns cases that cited the seed, with treatment details.

    """
    q = """
        MATCH (s:Case)-[r:TREATED_BY]->(t:Case {doc_id: $sid})
        RETURN s.doc_id        AS source,
               r.treatment_type AS citation_type,
               r.evidence       AS evidence,
               r.effective_date AS effective_date
    """
    with _get_driver().session() as session:
        return [dict(r) for r in session.run(q, sid=seed_id)]

#Edges having attributes. - Edges treated as DATA. (Triplet-Granular retrieval)
def neo4j_legislation(seed_id: str):

    #Captures the right hand side of the triplet (The edge + The target node with their attributes) - Seed is the source node (left hand side of the triplet)

    """
    Direct INVOLVES_ACT *1..1.
    Returns Act nodes with section from the edge.

    """
    q = """
        MATCH (s:Case {doc_id: $sid})-[r:INVOLVES_ACT]->(a:Act)
        RETURN a.act_id  AS act_id,
               a.name    AS name,
               r.section AS section
    """
    with _get_driver().session() as session:
        return [dict(r) for r in session.run(q, sid=seed_id)]

#Structural traversal edges with no edge properties naturally. - Edges treated as STRUCTURE.
def neo4j_appeal_chain(seed_id: str):
    """
    Bidirectional APPEALED_FROM *0..3, in higher court -> lower court direction
    (:SC Case)-[:APPEALED_FROM]->(:CA Case)-[:APPEALED_FROM]->(:DC Case)
    Undirected (-) captures both upward and downward traversal from seed.
    OPTIONAL MATCH on DECIDED_BY folds judge into each hop — no extra query.
    """
    q = """
        MATCH path = (seed:Case {doc_id: $sid})
                     -[:APPEALED_FROM*0..3]-(related:Case)
        WHERE related.doc_id <> $sid
        OPTIONAL MATCH (related)-[:DECIDED_BY]->(j:Judge)
        RETURN related.doc_id AS related,
               length(path)   AS hops,
               related.court  AS court,
               j.name         AS judge
    """
    with _get_driver().session() as session:
        return [dict(r) for r in session.run(q, sid=seed_id)]