"""
Fetch all 191 cases from Component A's /cases/{doc_id}/sections endpoint
and ingest body text into ChromaDB under COLLECTION_GENERIC.

"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from config import COLLECTION_GENERIC
from retrieval.seed.dense_retriever import DenseRetriever

BASE_URL = "https://component-a-api.onrender.com"

def fetch_all_cases() -> list[dict]:
    resp = httpx.get(f"{BASE_URL}/cases?limit=190&in_corpus=true", timeout=60)
    resp.raise_for_status()
    return resp.json()["cases"]

def build_text(sections: dict) -> str:
    parts = []
    for key in ("caption", "header", "body", "conclusion"):
        val = sections.get(key, {})
        if isinstance(val, dict):
            val = val.get("text", "")
        if val:
            parts.append(val.strip())
    return "\n\n".join(parts)

def main():
    print("Fetching all cases...")
    cases = fetch_all_cases()
    print(f"  {len(cases)} cases returned")

    corpus = []
    for case in cases:
        doc_id = case.get("doc_id")
        sections = case.get("sections")
        if not sections:
            continue
        text = build_text(sections)
        if text:
            corpus.append({"id": doc_id, "text": text})

    print(f"Built corpus: {len(corpus)} cases. Ingesting...")
    retriever = DenseRetriever(
        mode="generic",
        collection_name=COLLECTION_GENERIC,
        chroma_path="./chroma_db",
    )
    retriever.index_corpus(corpus)
    print(f"Done. {len(corpus)} cases indexed under '{COLLECTION_GENERIC}'.")

if __name__ == "__main__":
    main()