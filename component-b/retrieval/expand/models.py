from dataclasses import dataclass, field
from typing import List, Optional

#Output contract — Edges treated as data objects passed to Component C


@dataclass
class CitationEdge:
    target_id:      str
    citation_type:  str              #Followed | Distinguished | Overruled | Doubted
    evidence:       Optional[str] = None   ##Verbatim sentence from source judgment that establishes the citation
    scope:          Optional[str] = None   #Whether a citation is Ratio Decendi or Obiter Dictum which downstream RAG needs to know to determine the legal weight of the citation.
    effective_date: Optional[str] = None   #date treatment took effect


@dataclass
class LegislationEdge:
    act_id:  str                     #Act.act_id
    name:    str                     #Act.name
    section: Optional[str] = None   #INVOLVES_ACT.section


@dataclass
class AppealEdge:
    related_id: str
    hops:       int                  #traversal depth in appeal chain (Direct or further up and down the appeal chain)
    court:      Optional[str] = None   #SC | CA | HC | DC | MC
    judge:      Optional[str] = None   #Presiding judge at this appeal stage


@dataclass
class PrecedentCluster:
    seed_id:      str
    cases_cited:  List[CitationEdge]    = field(default_factory=list)  #Outgoing *1..2
    cited_by:     List[CitationEdge]    = field(default_factory=list)  #Incoming *1..1
    legislation:  List[LegislationEdge] = field(default_factory=list)  #INVOLVES_ACT *1..1
    appeal_chain: List[AppealEdge]      = field(default_factory=list)  #APPEALED_FROM *1..3 bidir
    rrf_score:    float                 = 0.0