from dotenv import load_dotenv
import os, json, random
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

samples = []

with driver.session() as s:
    for treatment_type, limit in [
        ("followed", 20),
        ("distinguished", 5),
        ("overruled", 3),
        ("doubted", 2)
    ]:
        rows = s.run("""
            MATCH (a:Case)-[t:TREATED_BY]->(b:Case)
            WHERE t.treatment_type = $type
            RETURN a.doc_id        AS treating_doc,
                   a.case_num      AS treating_num,
                   b.case_name     AS cited_name,
                   t.treatment_type AS type,
                   t.effective_date AS date,
                   t.evidence       AS evidence,
                   t.char_offset    AS offset
            LIMIT $limit
        """, type=treatment_type, limit=limit).data()
        samples.extend(rows)

driver.close()

# Save to JSON for annotation
with open("analysis/annotation_sample.json", "w", encoding="utf-8") as f:
    json.dump(samples, f, indent=2, ensure_ascii=False)

print(f"Saved {len(samples)} edges for annotation")
print()

# Print for manual review
for i, e in enumerate(samples, 1):
    print(f"--- EDGE {i} [{e['type'].upper()}] ---")
    print(f"Treating : {e['treating_num']}")
    print(f"Cited    : {e['cited_name']}")
    print(f"Evidence : {e['evidence'][:250] if e['evidence'] else 'NONE'}")
    print()