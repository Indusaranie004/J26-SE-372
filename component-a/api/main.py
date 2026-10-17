import sqlite3
import json
import os
import re
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

MOCK_MODE = os.getenv("COMPONENT_A_MOCK", "true").lower() == "true"

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import mock_data

# ── Neo4j driver (only used when MOCK_MODE=false) ─────────────────
_driver = None
def get_driver():
    global _driver
    if _driver is None:
        from neo4j import GraphDatabase
        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
    return _driver

# ── SQLite helper ─────────────────────────────────────────────────
DB_PATH    = "corpus/cases.db"
CASES_DIR  = "corpus/cases"
STUBS_DIR  = "corpus/stubs"

def get_case_from_db(doc_id: str):
    """Read case JSON from document store."""
    path = os.path.join(CASES_DIR, f"{doc_id}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return None

def get_stub_from_db(doc_id: str):
    """Read stub JSON from stubs folder."""
    path = os.path.join(STUBS_DIR, f"{doc_id}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return None

def get_citations_from_neo4j(doc_id: str, citation_type: str = None):
    """Query Neo4j for TREATED_BY edges from this case."""
    query = """
        MATCH (c:Case {doc_id: $doc_id})-[t:TREATED_BY]->(cited:Case)
        RETURN cited.doc_id   AS target_doc_id,
               cited.case_name AS target_case_name,
               cited.case_num  AS target_case_num,
               cited.in_corpus AS in_corpus,
               t.treatment_type  AS citation_type,
               t.effective_date  AS effective_date,
               t.evidence        AS evidence,
               t.char_offset     AS char_offset
    """
    with get_driver().session() as s:
        results = s.run(query, doc_id=doc_id)
        citations = []
        for r in results:
            c = dict(r)
            if citation_type and c["citation_type"] != citation_type:
                continue
            citations.append(c)
    return citations

def get_validity_from_neo4j(doc_id: str, as_of: str = None):
    """Query Neo4j for validity status of a case."""
    with get_driver().session() as s:
        result = s.run("""
            MATCH (c:Case {doc_id: $doc_id})
            OPTIONAL MATCH (c)<-[t:TREATED_BY]-(later:Case)
            RETURN c.validity_status AS status,
                   c.valid_from      AS valid_from,
                   c.valid_until     AS valid_until,
                   collect({
                       by:   later.doc_id,
                       type: t.treatment_type,
                       date: t.effective_date,
                       evidence: t.evidence
                   }) AS treatments
        """, doc_id=doc_id).single()

        if not result:
            return None

        treatments = [t for t in result["treatments"] if t.get("by")]

        if as_of:
            treatments = [t for t in treatments
                         if t.get("date") and t["date"] <= as_of]
            types = [t["type"] for t in treatments]
            if "overruled" in types:
                status = "no_longer_good_law"
                safe = False
            elif "distinguished" in types or "doubted" in types:
                status = "partially_invalidated"
                safe = True
            else:
                status = "good_law"
                safe = True
        else:
            status = result["status"] or "good_law"
            safe = status == "good_law"

        return {
            "doc_id":             doc_id,
            "validity_status":    status,
            "valid_from":         result["valid_from"],
            "valid_until":        result["valid_until"],
            "treatments_received": treatments,
            "safe_to_cite":       safe,
            "as_of":              as_of or "current"
        }

app = FastAPI(
    title="Component A — Precedent Validity Knowledge Graph API",
    version="0.1.0-mock" if MOCK_MODE else "0.1.0",
    description="Knowledge graph, vector store and document store for Sri Lankan case law."
)

# ── MANIFEST ──────────────────────────────────────────────────────

@app.get("/manifest")
def get_manifest():
    if MOCK_MODE:
        return {
            "corpus_version": "2026.10-mock",
            "sc_documents": 3,
            "mock_mode": True,
            "doc_ids": list(mock_data.CASES.keys())
        }
    try:
        con = sqlite3.connect(DB_PATH)
        count = con.execute(
            "SELECT count(*) FROM cases WHERE in_corpus=1"
        ).fetchone()[0]
        doc_ids = [r[0] for r in con.execute(
            "SELECT doc_id FROM cases WHERE in_corpus=1"
        ).fetchall()]
        con.close()
    except Exception:
        count = 0
        doc_ids = []
    return {
        "corpus_version": "2026.10",
        "sc_documents": count,
        "mock_mode": False,
        "doc_ids": doc_ids
    }

# ── HEALTH ────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": MOCK_MODE}

# ── CASES ─────────────────────────────────────────────────────────

@app.get("/cases/{doc_id}")
def get_case(doc_id: str):
    if MOCK_MODE:
        if doc_id in mock_data.STUBS:
            return mock_data.STUBS[doc_id]
        if doc_id not in mock_data.CASES:
            raise HTTPException(status_code=404, detail={
                "error": "case_not_found", "doc_id": doc_id,
                "message": f"No case found for {doc_id}."
            })
        return mock_data.CASES[doc_id]

    # Live mode — read from document store
    record = get_case_from_db(doc_id)
    if record:
        return record
    stub = get_stub_from_db(doc_id)
    if stub:
        return stub
    raise HTTPException(status_code=404, detail={
        "error": "case_not_found", "doc_id": doc_id,
        "message": f"No case found for {doc_id}. "
                   f"If cited but not in corpus check /stubs/{doc_id}"
    })

# ── STUBS ─────────────────────────────────────────────────────────

@app.get("/stubs/{doc_id}")
def get_stub(doc_id: str):
    if MOCK_MODE:
        if doc_id not in mock_data.STUBS:
            raise HTTPException(status_code=404, detail={
                "error": "stub_not_found", "doc_id": doc_id
            })
        return mock_data.STUBS[doc_id]

    stub = get_stub_from_db(doc_id)
    if not stub:
        raise HTTPException(status_code=404, detail={
            "error": "stub_not_found", "doc_id": doc_id,
            "message": f"No stub found for {doc_id}."
        })
    return stub

# ── SECTIONS ──────────────────────────────────────────────────────

@app.get("/cases/{doc_id}/sections/{section_name}")
def get_section(doc_id: str, section_name: str):
    valid_sections = ["caption", "header", "body", "conclusion"]
    if section_name not in valid_sections:
        raise HTTPException(status_code=422, detail={
            "error": "invalid_section",
            "section": section_name,
            "valid_sections": valid_sections
        })

    if MOCK_MODE:
        if doc_id not in mock_data.CASES:
            raise HTTPException(status_code=404, detail={
                "error": "case_not_found", "doc_id": doc_id
            })
        case = mock_data.CASES[doc_id]
        if not case.get("text_available"):
            raise HTTPException(status_code=503, detail={
                "error": "text_unavailable",
                "ocr_required": case.get("ocr_required", False)
            })
        sections = case.get("sections", {})
        if section_name not in sections:
            raise HTTPException(status_code=404, detail={
                "error": "section_not_found",
                "available_sections": list(sections.keys())
            })
        return {"doc_id": doc_id, "section": section_name,
                **sections[section_name]}

    # Live mode
    record = get_case_from_db(doc_id)
    if not record:
        raise HTTPException(status_code=404, detail={
            "error": "case_not_found", "doc_id": doc_id
        })
    if not record.get("text_available"):
        raise HTTPException(status_code=503, detail={
            "error": "text_unavailable",
            "ocr_required": record.get("ocr_required", False),
            "message": "Text not available for this document."
        })
    sections = record.get("sections", {})
    if section_name not in sections:
        raise HTTPException(status_code=404, detail={
            "error": "section_not_found",
            "available_sections": list(sections.keys())
        })
    return {"doc_id": doc_id, "section": section_name,
            **sections[section_name]}

# ── CITATIONS ─────────────────────────────────────────────────────

@app.get("/cases/{doc_id}/citations")
def get_citations(
    doc_id: str,
    citation_type: Optional[str] = Query(None)
):
    valid_types = ["followed", "distinguished", "overruled",
                   "doubted", "per_incuriam", "unclassified"]
    if citation_type and citation_type not in valid_types:
        raise HTTPException(status_code=422, detail={
            "error": "invalid_citation_type",
            "valid_types": valid_types
        })

    if MOCK_MODE:
        if doc_id not in mock_data.CASES and doc_id not in mock_data.STUBS:
            raise HTTPException(status_code=404, detail={
                "error": "case_not_found", "doc_id": doc_id
            })
        citations = mock_data.CITATIONS.get(doc_id, [])
        if citation_type:
            citations = [c for c in citations
                        if c["citation_type"] == citation_type]
        return {"doc_id": doc_id, "count": len(citations),
                "citations": citations}

    # Live mode — query Neo4j
    try:
        citations = get_citations_from_neo4j(doc_id, citation_type)
        return {"doc_id": doc_id, "count": len(citations),
                "citations": citations}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

# ── VALIDITY ──────────────────────────────────────────────────────

@app.get("/cases/{doc_id}/validity")
def get_validity(
    doc_id: str,
    as_of: Optional[str] = Query(None)
):
    if as_of and not re.match(r'^\d{4}-\d{2}-\d{2}$', as_of):
        raise HTTPException(status_code=422, detail={
            "error": "invalid_date_format",
            "expected": "YYYY-MM-DD"
        })

    if MOCK_MODE:
        if doc_id in mock_data.STUBS:
            stub = mock_data.STUBS[doc_id]
            return {**stub, "as_of": as_of}
        if doc_id not in mock_data.CASES:
            raise HTTPException(status_code=404, detail={
                "error": "case_not_found", "doc_id": doc_id
            })
        validity = dict(mock_data.VALIDITY.get(doc_id, {
            "validity_status": "good_law",
            "treatments_received": [],
            "safe_to_cite": True
        }))
        validity["as_of"] = as_of or "current"
        return validity

    # Live mode — query Neo4j
    try:
        result = get_validity_from_neo4j(doc_id, as_of)
        if not result:
            raise HTTPException(status_code=404, detail={
                "error": "case_not_found", "doc_id": doc_id
            })
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

# ── CHAIN ─────────────────────────────────────────────────────────

@app.get("/cases/{doc_id}/chain")
def get_chain(doc_id: str):
    if MOCK_MODE:
        if doc_id not in mock_data.CASES and doc_id not in mock_data.STUBS:
            raise HTTPException(status_code=404, detail={
                "error": "case_not_found", "doc_id": doc_id
            })
        chain_data = mock_data.CHAINS.get(
            doc_id, {"doc_id": doc_id, "chain": []}
        )
        return chain_data

    # Live mode — read from Neo4j APPEALED_FROM edges
    try:
        with get_driver().session() as s:
            rows = s.run("""
                MATCH (c:Case {doc_id: $doc_id})-[:APPEALED_FROM]->(lower:Case)
                RETURN lower.court    AS court,
                       lower.case_num AS num,
                       lower.place    AS place,
                       lower.in_corpus AS in_corpus
            """, doc_id=doc_id).data()

        if not rows:
            # Fallback to document store if no KG chain
            record = get_case_from_db(doc_id)
            if record:
                return {
                    "doc_id": doc_id,
                    "source": "document_store",
                    "chain": record.get("chain", [])
                }
            return {"doc_id": doc_id, "source": "knowledge_graph", "chain": []}

        return {
            "doc_id": doc_id,
            "source": "knowledge_graph",
            "chain": rows
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

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
        raise HTTPException(status_code=422, detail={
            "error": "empty_query"
        })
    if request.mode not in valid_modes:
        raise HTTPException(status_code=422, detail={
            "error": "invalid_mode",
            "valid_modes": valid_modes
        })

    top_k = max(1, min(20, request.top_k or 5))

    if MOCK_MODE:
        query_lower = request.query.lower()
        results = []
        for key, hits in mock_data.SEARCH_RESULTS.items():
            if any(word in query_lower for word in key.split()):
                results = hits
                break
        return {
            "query": request.query,
            "mode": request.mode,
            "count": len(results[:top_k]),
            "results": results[:top_k],
            "corpus_version": "2026.10-mock"
        }

    # Live mode — SQLite FTS search
    try:
        con = sqlite3.connect(DB_PATH)
        rows = con.execute("""
            SELECT doc_id, snippet(cases_fts, 2, '', '', '...', 20) AS snippet
            FROM cases_fts
            WHERE text MATCH ?
            LIMIT ?
        """, (request.query, top_k)).fetchall()
        con.close()
        results = [{"doc_id": r[0], "snippet": r[1]} for r in rows]
        return {
            "query": request.query,
            "mode": request.mode,
            "count": len(results),
            "results": results,
            "corpus_version": "2026.10"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

# ── AGENT ─────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    question: str

@app.post("/agent/ask")
def agent_ask(request: AgentRequest):
    if not request.question.strip():
        raise HTTPException(status_code=422, detail={
            "error": "empty_question"
        })

    if MOCK_MODE:
        q = request.question.lower()
        all_records = {**mock_data.CASES, **mock_data.STUBS}
        matched_id = None
        for doc_id, case in all_records.items():
            searchable = []
            if case.get("case_num"):
                searchable.append(case["case_num"].lower())
            if case.get("case_name"):
                searchable.append(case["case_name"].lower())
            name = (case.get("case_name") or case.get("case_num") or "")
            for word in name.lower().split():
                if len(word) > 4:
                    searchable.append(word)
            if any(s in q for s in searchable):
                matched_id = doc_id
                break

        if not matched_id:
            return {
                "answer": "Could not identify a specific case. "
                         "Try including the case name or number.",
                "confidence": "low"
            }
        validity = mock_data.VALIDITY.get(matched_id) or \
                   all_records.get(matched_id, {})
        status = validity.get("validity_status", "good_law")
        answer = {
            "no_longer_good_law": "❌ NO LONGER GOOD LAW. Do not cite.",
            "partially_invalidated": "⚠ Partially qualified. Review before citing.",
        }.get(status, "✅ GOOD LAW. Safe to cite.")
        return {
            "doc_id": matched_id,
            "status": status,
            "answer": answer,
            "safe_to_cite": status == "good_law",
            "treatments_received": validity.get("treatments_received", [])
        }

    # Live mode — query Neo4j directly
    try:
        import re as re2
        case_rx = re2.search(
            r'([A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+|SC[/\s]\w+[/\s]\d+[/\s]\d+)',
            request.question
        )
        if not case_rx:
            return {
                "answer": "Could not identify a case. "
                         "Try including the case name or SC case number.",
                "confidence": "low"
            }
        ref = case_rx.group(1)
        with get_driver().session() as s:
            result = s.run("""
                MATCH (c:Case)
                WHERE c.case_num CONTAINS $ref
                   OR c.case_name CONTAINS $ref
                OPTIONAL MATCH (c)<-[t:TREATED_BY]-(later:Case)
                RETURN c.doc_id AS doc_id,
                       c.case_num AS case_num,
                       c.validity_status AS status,
                       collect({
                           by: later.case_num,
                           type: t.treatment_type,
                           date: t.effective_date
                       }) AS treatments
                LIMIT 1
            """, ref=ref).single()

        if not result:
            return {
                "answer": f"No case matching '{ref}' found in the corpus.",
                "confidence": "low"
            }

        status = result["status"] or "good_law"
        treatments = [t for t in result["treatments"] if t.get("by")]
        answer = {
            "no_longer_good_law": "❌ NO LONGER GOOD LAW. Do not cite.",
            "partially_invalidated": "⚠ Partially qualified. Review before citing.",
        }.get(status, "✅ GOOD LAW. Safe to cite.")

        return {
            "doc_id": result["doc_id"],
            "case": result["case_num"],
            "status": status,
            "answer": answer,
            "safe_to_cite": status == "good_law",
            "treatments_received": treatments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})