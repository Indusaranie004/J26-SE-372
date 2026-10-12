import os
import re
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

MOCK_MODE = os.getenv("COMPONENT_A_MOCK", "true").lower() == "true"

# import mock data
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import mock_data

app = FastAPI(
    title="Component A — Precedent Validity Knowledge Graph API",
    version="0.1.0-mock" if MOCK_MODE else "0.1.0",
    description="Knowledge graph, vector store and document store for Sri Lankan case law."
)

# ── MANIFEST ──────────────────────────────────────────────────────

@app.get("/manifest")
def get_manifest():
    return {
        "corpus_version": "2026.10-mock",
        "sc_documents": 3,
        "ca_documents": 0,
        "sc_sha": "a3f9c1e7b2d4e8f0c6a1b3d5e7f9c2a4",
        "built_at": "2026-10-07T10:00:00",
        "mock_mode": MOCK_MODE
    }

# ── HEALTH ────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": MOCK_MODE}

# ── CASES ─────────────────────────────────────────────────────────

@app.get("/cases/{doc_id}")
def get_case(doc_id: str):
    if doc_id in mock_data.STUBS:
        return mock_data.STUBS[doc_id]
    if doc_id not in mock_data.CASES:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "case_not_found",
                "doc_id": doc_id,
                "message": f"No case found for {doc_id}. "
                           f"If cited but not in corpus check /stubs/{doc_id}"
            }
        )
    return mock_data.CASES[doc_id]

# ── STUBS ─────────────────────────────────────────────────────────

@app.get("/stubs/{doc_id}")
def get_stub(doc_id: str):
    if doc_id not in mock_data.STUBS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "stub_not_found",
                "doc_id": doc_id,
                "message": f"No stub found for {doc_id}. "
                           f"If in corpus use /cases/{doc_id}"
            }
        )
    return mock_data.STUBS[doc_id]

# ── SECTIONS ──────────────────────────────────────────────────────

@app.get("/cases/{doc_id}/sections/{section_name}")
def get_section(doc_id: str, section_name: str):
    valid_sections = ["caption", "header", "body", "conclusion"]

    if section_name not in valid_sections:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_section",
                "section": section_name,
                "valid_sections": valid_sections
            }
        )
    if doc_id not in mock_data.CASES:
        raise HTTPException(
            status_code=404,
            detail={"error": "case_not_found", "doc_id": doc_id}
        )

    case = mock_data.CASES[doc_id]

    if not case.get("text_available"):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "text_unavailable",
                "doc_id": doc_id,
                "ocr_required": case.get("ocr_required", False),
                "message": "Full text not yet extracted. OCR processing pending."
            }
        )

    sections = case.get("sections", {})
    if section_name not in sections:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "section_not_found",
                "doc_id": doc_id,
                "section": section_name,
                "available_sections": list(sections.keys())
            }
        )

    return {"doc_id": doc_id, "section": section_name, **sections[section_name]}

# ── CITATIONS ─────────────────────────────────────────────────────

@app.get("/cases/{doc_id}/citations")
def get_citations(
    doc_id: str,
    citation_type: Optional[str] = Query(
        None,
        description="Filter: followed | distinguished | overruled | doubted"
    )
):
    valid_types = ["followed", "distinguished", "overruled",
                   "doubted", "per_incuriam", "unclassified"]

    if citation_type and citation_type not in valid_types:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_citation_type",
                "provided": citation_type,
                "valid_types": valid_types
            }
        )

    if doc_id not in mock_data.CASES and doc_id not in mock_data.STUBS:
        raise HTTPException(
            status_code=404,
            detail={"error": "case_not_found", "doc_id": doc_id}
        )

    citations = mock_data.CITATIONS.get(doc_id, [])
    if citation_type:
        citations = [c for c in citations if c["citation_type"] == citation_type]

    return {"doc_id": doc_id, "count": len(citations), "citations": citations}

# ── VALIDITY ──────────────────────────────────────────────────────

@app.get("/cases/{doc_id}/validity")
def get_validity(
    doc_id: str,
    as_of: Optional[str] = Query(
        None,
        description="Date YYYY-MM-DD — returns validity as at that date"
    )
):
    if as_of and not re.match(r'^\d{4}-\d{2}-\d{2}$', as_of):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_date_format",
                "provided": as_of,
                "expected": "YYYY-MM-DD"
            }
        )

    # check stubs first
    if doc_id in mock_data.STUBS:
        stub = mock_data.STUBS[doc_id]
        if as_of and as_of < stub.get("valid_from", "1900-01-01"):
            return {
                "doc_id": doc_id,
                "as_of": as_of,
                "validity_status": "not_yet_decided",
                "message": f"Case decided on {stub.get('valid_from')}. "
                           f"Did not exist as at {as_of}."
            }
        return {**stub, "as_of": as_of}

    if doc_id not in mock_data.CASES:
        raise HTTPException(
            status_code=404,
            detail={"error": "case_not_found", "doc_id": doc_id}
        )

    if doc_id not in mock_data.VALIDITY:
        return {
            "doc_id": doc_id,
            "validity_status": "good_law",
            "valid_from": mock_data.CASES[doc_id]["date"],
            "valid_until": None,
            "treatments_received": [],
            "safe_to_cite": True,
            "as_of": as_of,
            "summary": "No treatments recorded. Good law."
        }

    validity = dict(mock_data.VALIDITY[doc_id])

    if as_of:
        validity["treatments_received"] = [
            t for t in validity["treatments_received"]
            if t["date"] <= as_of
        ]
        types = [t["type"] for t in validity["treatments_received"]]
        if "overruled" in types:
            validity["validity_status"] = "no_longer_good_law"
            validity["safe_to_cite"] = False
        elif "distinguished" in types or "doubted" in types:
            validity["validity_status"] = "partially_invalidated"
            validity["safe_to_cite"] = True
        else:
            validity["validity_status"] = "good_law"
            validity["safe_to_cite"] = True

    validity["as_of"] = as_of or "current"
    return validity

# ── CHAIN ─────────────────────────────────────────────────────────

@app.get("/cases/{doc_id}/chain")
def get_chain(doc_id: str):
    if doc_id not in mock_data.CASES and doc_id not in mock_data.STUBS:
        raise HTTPException(
            status_code=404,
            detail={"error": "case_not_found", "doc_id": doc_id}
        )

    chain_data = mock_data.CHAINS.get(
        doc_id, {"doc_id": doc_id, "chain": []}
    )

    if not chain_data["chain"]:
        return {
            **chain_data,
            "note": "No litigation chain data found for this case."
        }

    return chain_data

# ── SEARCH ────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    mode: Optional[str] = "hybrid"
    filters: Optional[dict] = {}
    top_k: Optional[int] = 5

@app.post("/search")
def search(request: SearchRequest):
    valid_modes = ["hybrid", "semantic", "keyword", "graph"]

    if not request.query.strip():
        raise HTTPException(
            status_code=422,
            detail={"error": "empty_query",
                    "message": "Query string cannot be empty."}
        )

    if request.mode not in valid_modes:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_mode",
                    "provided": request.mode,
                    "valid_modes": valid_modes}
        )

    top_k = max(1, min(20, request.top_k or 5))
    query_lower = request.query.lower()
    results = []

    for key, hits in mock_data.SEARCH_RESULTS.items():
        if any(word in query_lower for word in key.split()):
            results = hits
            break

    if request.filters.get("valid_only"):
        results = [
            r for r in results
            if mock_data.VALIDITY.get(
                r["doc_id"], {}
            ).get("safe_to_cite", True)
        ]

    return {
        "query": request.query,
        "mode": request.mode,
        "count": len(results[:top_k]),
        "results": results[:top_k],
        "corpus_version": "2026.10-mock"
    }

# ── AGENT ─────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    question: str

@app.post("/agent/ask")
def agent_ask(request: AgentRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=422,
            detail={"error": "empty_question"}
        )

    q = request.question.lower()
    matched_id = None

    # Check against case_num, case_name, and common name fragments
    all_records = {
        **mock_data.CASES,
        **mock_data.STUBS
    }

    for doc_id, case in all_records.items():
        # Build a list of things to match against
        searchable = []

        if case.get("case_num"):
            searchable.append(case["case_num"].lower())
        if case.get("case_name"):
            searchable.append(case["case_name"].lower())

        # Also match on party name fragments
        # e.g. "Fernando" matches "Fernando v. Attorney General"
        name = (case.get("case_name") or case.get("case_num") or "")
        for word in name.lower().split():
            if len(word) > 4:  # skip short words like "v." "the"
                searchable.append(word)

        if any(s in q for s in searchable):
            matched_id = doc_id
            break

    if not matched_id:
        return {
            "answer": "I could not identify a specific case in your question. "
                     "Try including the case name such as 'Fernando v AG' "
                     "or a case number such as 'SC/FR/7/2023'.",
            "confidence": "low",
            "tip": "Available cases: Fernando v AG, Silva v AG, SC/FR/7/2023"
        }

    validity = mock_data.VALIDITY.get(matched_id) or all_records.get(matched_id, {})
    status = validity.get("validity_status", "good_law")

    if status == "no_longer_good_law":
        answer = "❌ This case is NO LONGER GOOD LAW. Do not cite."
        safe = False
    elif status == "partially_invalidated":
        answer = "⚠ This case has been partially qualified. Review before citing."
        safe = True
    else:
        answer = "✅ This case is GOOD LAW. Safe to cite."
        safe = True

    case_display = all_records[matched_id].get("case_name") or \
                   all_records[matched_id].get("case_num") or matched_id

    return {
        "doc_id": matched_id,
        "case": case_display,
        "status": status,
        "answer": answer,
        "safe_to_cite": safe,
        "treatments_received": validity.get("treatments_received", []),
        "summary": validity.get("summary", "")
    }