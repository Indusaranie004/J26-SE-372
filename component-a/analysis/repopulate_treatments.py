"""
Re-run treatment extraction on all corpus documents using the model.
Clears existing TREATED_BY edges first then repopulates.
"""
import os, json, glob, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from pymongo import MongoClient
from neo4j import GraphDatabase
from extraction.treatment_extractor_model import extract_treatments_model

load_dotenv()

def get_mongo():
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client["lk_legal"]

def get_driver():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )

def clear_treatment_edges(driver):
    with driver.session() as s:
        result = s.run("MATCH ()-[t:TREATED_BY]->() DELETE t RETURN count(t) AS deleted")
        deleted = result.single()["deleted"]
        print(f"Cleared {deleted} existing TREATED_BY edges")

def write_treatment_edge(driver, doc_id, treated_case, treatment_type,
                         date, evidence, char_offset, confidence=None):
    from extraction.neo4j_writer import write_treatment_edge as _write
    _write(doc_id, treated_case, treatment_type, date, evidence, char_offset)

def run(limit=None):
    print("Loading model...")
    from extraction.treatment_extractor_model import get_classifier
    classifier = get_classifier()
    if classifier is None:
        print("ERROR: Model not loaded. Check model/treatment_classifier/ exists.")
        return

    db     = get_mongo()
    driver = get_driver()

    # Clear existing edges
    clear_treatment_edges(driver)

    # Get all corpus cases from MongoDB
    query  = {"in_corpus": True}
    cursor = db["cases"].find(query, {"doc_id": 1, "date": 1, "sections": 1, "entities": 1})
    cases  = list(cursor)
    if limit:
        cases = cases[:limit]

    print(f"Re-extracting treatments for {len(cases)} cases...")

    total_edges = 0
    errors      = 0

    for i, rec in enumerate(cases):
        doc_id    = rec["doc_id"]
        date      = rec.get("date", "unknown")
        body_text = rec.get("sections", {}).get("body", {}).get("text", "")
        body_start = rec.get("sections", {}).get("body", {}).get("char_start", 0)

        if not body_text:
            continue

        citations = []
        for c in rec.get("entities", {}).get("citations", []):
            citations.append({
                "text":        c["text"],
                "start":       c["start"],
                "body_offset": max(0, c["start"] - body_start)
            })

        try:
            treatments = extract_treatments_model(body_text, doc_id, citations)
            for t in treatments:
                from extraction.neo4j_writer import write_treatment_edge
                write_treatment_edge(
                    doc_id,
                    t["treated_case_name"],
                    t["treatment_type"],
                    date,
                    t["evidence"],
                    t["char_offset"]
                )
                total_edges += 1
        except Exception as e:
            errors += 1
            print(f"Error on {doc_id}: {e}")

        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(cases)} — {total_edges} edges so far")

    driver.close()
    print(f"\nDone — {total_edges} treatment edges written, {errors} errors")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(args.limit)