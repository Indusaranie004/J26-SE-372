from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

with driver.session() as s:
    edges = s.run("""
        MATCH (a:Case)-[t:TREATED_BY]->(b:Case)
        RETURN a.doc_id        AS treating_doc,
               a.case_num      AS treating_num,
               b.case_name     AS cited_name,
               b.in_corpus     AS cited_in_corpus,
               t.treatment_type AS type,
               t.effective_date AS date,
               t.evidence       AS evidence,
               t.char_offset    AS offset
        LIMIT 20
    """).data()

print(f"Checking {len(edges)} TREATED_BY edges\n")
print("="*70)

for i, e in enumerate(edges, 1):
    print(f"\nEDGE {i}")
    print(f"Treating case : {e['treating_num']} ({e['treating_doc']})")
    print(f"Cited case    : {e['cited_name']}")
    print(f"In corpus     : {e['cited_in_corpus']}")
    print(f"Treatment type: {e['type']}")
    print(f"Effective date: {e['date']}")
    print(f"Char offset   : {e['offset']}")
    print(f"Evidence      : {e['evidence'][:300] if e['evidence'] else 'NONE'}")
    print("-"*70)

driver.close()