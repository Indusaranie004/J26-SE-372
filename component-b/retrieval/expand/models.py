from dataclasses import dataclass, field
from typing import List, Optional

#Output contract for the clusters passed to Component C


@dataclass
class CitationEdge:
    target_id:      str
    citation_type:  str              #Followed | Distinguished | Overruled | Doubted
    direction:      str              #cases_cited | cited_by
    evidence:       Optional[str] = None   ##erbatim sentence from source judgment that establishes the citation
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
class LegalContext:
    judicial_treatment:     List[CitationEdge]    = field(default_factory=list)  #cases_cited (Outgoing *1..2) + cited_by (Incoming *1..1)
    legislative_foundation: List[LegislationEdge] = field(default_factory=list)  #INVOLVES_ACT *1..1
    litigation_history:     List[AppealEdge]      = field(default_factory=list)  #APPEALED_FROM *1..3 bidir


@dataclass
class PrecedentCluster:
    seed_id:       str
    legal_context: LegalContext = field(default_factory=LegalContext)
    rrf_score:     float        = 0.0