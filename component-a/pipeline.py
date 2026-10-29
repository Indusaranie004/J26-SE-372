"""
Unified pipeline runner — ingest new documents and populate KG.
Run manually or schedule via cron/Render job.

Usage:
    python pipeline.py --corpus ../lk_court_of_appeal_judgements --limit 100
    python pipeline.py --corpus ../lk_supreme_court_judgements --limit 500
"""
import os, json, glob, argparse
from datetime import datetime
from extraction.document_store import init_db, ingest_document
from extraction.neo4j_writer import (
    init_constraints, write_case_node, write_judge_edge,
    write_act_edge, write_treatment_edge, write_chain_edges
)
from extraction.treatment_extractor_model import extract_treatments_model
from extraction.chain_parser import parse_chain_from_caption
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_mongo():
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client["lk_legal"]

def get_processed_ids():
    """Get doc_ids already in MongoDB to skip re-processing."""
    db = get_mongo()
    return set(r["_id"] for r in db["cases"].find({}, {"_id": 1}))

def ingest_to_mongodb(record):
    """Upload a single case record to MongoDB."""
    db = get_mongo()
    doc = dict(record)
    doc["_id"] = doc["doc_id"]
    db["cases"].update_one(
        {"_id": doc["_id"]},
        {"$set": doc},
        upsert=True
    )

def read_text_from_blocks(folder_path):
    """Extract full text from blocks.json when doc.txt is unavailable."""
    blocks_path = os.path.join(folder_path, "blocks.json")
    if not os.path.exists(blocks_path):
        return None
    try:
        blocks = json.load(open(blocks_path, encoding="utf-8"))
        blocks.sort(key=lambda b: (
            b.get("page_number", 0),
            -b.get("bbox", [0, 0, 0, 0])[3]
        ))
        text = " ".join(
            b["text"] for b in blocks if b.get("text", "").strip()
        )
        return text if len(text) > 100 else None
    except Exception:
        return None

def get_all_folders(corpus_path):
    """Scan corpus including nested decade/year subfolders."""
    folders = []

    # Check if corpus has decade subfolders (2000s, 2010s, 2020s)
    decade_dirs = [
        d for d in os.listdir(corpus_path)
        if os.path.isdir(os.path.join(corpus_path, d))
        and d.endswith("s")
        and d[:4].isdigit()
    ]

    if decade_dirs:
        # Nested structure: corpus/2020s/2023/doc_folder/
        for decade in sorted(decade_dirs):
            decade_path = os.path.join(corpus_path, decade)
            for year_dir in sorted(os.listdir(decade_path)):
                year_path = os.path.join(decade_path, year_dir)
                if not os.path.isdir(year_path):
                    continue
                for doc_dir in sorted(os.listdir(year_path)):
                    doc_path = os.path.join(year_path, doc_dir)
                    if os.path.isdir(doc_path):
                        folders.append(doc_path)
    else:
        # Flat structure: corpus/doc_folder/
        folders = [
            os.path.join(corpus_path, d)
            for d in sorted(os.listdir(corpus_path))
            if os.path.isdir(os.path.join(corpus_path, d))
        ]

    return folders

def populate_neo4j(rec):
    """Write a single case record to Neo4j."""
    doc_id   = rec["doc_id"]
    case_num = rec.get("case_num", doc_id)
    court    = rec.get("court", "SC")
    date     = rec.get("date", "unknown")

    write_case_node(doc_id, case_num, court, date)

    for judge in rec["entities"].get("judges", []):
        write_judge_edge(doc_id, judge["text"])

    for act in rec["entities"].get("acts", []):
        write_act_edge(doc_id, act["text"],
                      act.get("act_year"),
                      act.get("section"),
                      act.get("act_number"))

    caption_text = rec["sections"].get("caption", {}).get("text", "")
    chain = parse_chain_from_caption(caption_text)
    if chain:
        write_chain_edges(doc_id, chain)

    body_text  = rec["sections"].get("body", {}).get("text", "")
    body_start = rec["sections"].get("body", {}).get("char_start", 0)
    citations  = []
    for c in rec["entities"].get("citations", []):
        citations.append({
            "text":        c["text"],
            "start":       c["start"],
            "body_offset": max(0, c["start"] - body_start)
        })

    treatments = extract_treatments_model(body_text, doc_id, citations)
    for t in treatments:
        write_treatment_edge(
            doc_id,
            t["treated_case_name"],
            t["treatment_type"],
            date,
            t["evidence"],
            t["char_offset"]
        )

    return len(treatments)

def run_pipeline(corpus_path, limit=None, court="SC"):
    print(f"Pipeline started: {datetime.now().isoformat()}")
    print(f"Corpus: {corpus_path}")
    print(f"Court: {court}")

    # Init
    init_constraints()
    init_db()

    # Get already processed IDs
    processed = get_processed_ids()
    print(f"Already processed: {len(processed)} documents")

    # Find all document folders including nested decade/year structure
    all_folders = get_all_folders(corpus_path)
    print(f"Total folders found: {len(all_folders)}")

    if limit:
        all_folders = all_folders[:limit]

    new_docs        = 0
    skipped         = 0
    no_text         = 0
    treatment_edges = 0
    errors          = 0

    for folder in all_folders:
        name   = os.path.basename(folder.rstrip("/").rstrip("\\"))
        doc_id = name

        if doc_id in processed:
            skipped += 1
            continue

        # Try doc.txt first, fall back to blocks.json
        text = None
        txt_path = os.path.join(folder, "doc.txt")
        if os.path.exists(txt_path):
            text = open(txt_path, encoding="utf-8", errors="ignore").read()

        if not text or len(text.strip()) < 100:
            text = read_text_from_blocks(folder)

        if not text or len(text.strip()) < 100:
            no_text += 1
            continue

        try:
            # Parse metadata from folder name
            parts    = name.split("-")
            date     = "-".join(parts[:3]) if len(parts) >= 3 else "unknown"
            case_num = name

            # Ingest
            record = ingest_document(
                text, doc_id, case_num, court, date,
                source_sha="pipeline"
            )

            # Upload to MongoDB
            ingest_to_mongodb(record)

            # Populate Neo4j
            n_treatments = populate_neo4j(record)
            treatment_edges += n_treatments
            new_docs += 1

            if new_docs % 50 == 0:
                print(f"  Processed {new_docs} new documents...")

        except Exception as e:
            errors += 1
            print(f"  Error on {doc_id}: {e}")
            continue

    print(f"\nPipeline complete: {datetime.now().isoformat()}")
    print(f"  Total folders:    {len(all_folders)}")
    print(f"  New documents:    {new_docs}")
    print(f"  Skipped:          {skipped}")
    print(f"  No text:          {no_text}")
    print(f"  Treatment edges:  {treatment_edges}")
    print(f"  Errors:           {errors}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--limit",  type=int, default=None)
    parser.add_argument("--court",  default="SC")
    args = parser.parse_args()
    run_pipeline(args.corpus, args.limit, args.court)