# component-d/issue_spotting/models.py
from pydantic import BaseModel, Field
from typing import List, Optional

class SubIssue(BaseModel):
    id: str = Field(..., description="Unique identifier e.g., i1, i1.1, i1.1.1")
    question: str = Field(..., description="Specific legal sub-question, MUST end with a '?'")
    research_question: str = Field(..., description="Question phrased for search engine retrieval")
    legal_elements: List[str] = Field(default_factory=list, description="Requirements to establish this issue")
    relevant_facts: List[str] = Field(default_factory=list, description="Facts explicitly stated by lawyer")
    missing_facts: List[str] = Field(default_factory=list, description="Critical facts not yet provided")
    applicable_law: List[str] = Field(default_factory=list, description="Statutes/Acts mentioned in query only")
    authority_hints: List[str] = Field(default_factory=list, description="Keywords/case names for Component B")
    status: str = Field("needs_facts", description="Either 'needs_facts' (Orange) or 'ready' (Green)")
    children: List['SubIssue'] = Field(default_factory=list, description="Nested sub-issues for deeper hierarchy")

class IssueTreeResponse(BaseModel):
    query: str = Field(..., description="Original user query")
    main_issue: str = Field(..., description="Central legal question, MUST end with a '?'")
    main_research_question: str = Field(..., description="Overarching research question for the whole case")
    global_missing_facts: List[str] = Field(default_factory=list, description="High-level missing facts for the sidebar")
    urgent: Optional[dict] = Field(None, description="Time-sensitive alerts (e.g., auction deadlines) for the red banner")
    issues: List[SubIssue] = Field(..., min_length=1, description="Top-level legal issues")