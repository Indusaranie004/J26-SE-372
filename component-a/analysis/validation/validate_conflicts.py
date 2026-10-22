from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

with driver.session() as s:

    print("=== CASES BOTH FOLLOWED AND OVERRULED ===")
    rows = s.run("""
        MATCH (a:Case)-[t1:TREATED_BY {treatment_type:'followed'}]->(b:Case)
        MATCH (c:Case)-[t2:TREATED_BY {treatment_type:'overruled'}]->(b)
        WHERE a <> c
        RETURN b.case_name AS case,
               a.doc_id AS followed_by,
               c.doc_id AS overruled_by,
               t1.effective_date AS followed_date,
               t2.effective_date AS overruled_date
    """).data()
    print(f"Found: {len(rows)}")
    for r in rows:
        print(f"  Case: {r['case']}")
        print(f"  Followed by:  {r['followed_by']} on {r['followed_date']}")
        print(f"  Overruled by: {r['overruled_by']} on {r['overruled_date']}")
        print()

    print("=== CASES BOTH FOLLOWED AND DOUBTED ===")
    rows = s.run("""
        MATCH (a:Case)-[t1:TREATED_BY {treatment_type:'followed'}]->(b:Case)
        MATCH (c:Case)-[t2:TREATED_BY {treatment_type:'doubted'}]->(b)
        WHERE a <> c
        RETURN b.case_name AS case,
               a.doc_id AS followed_by,
               c.doc_id AS doubted_by
    """).data()
    print(f"Found: {len(rows)}")
    for r in rows:
        print(f"  Case: {r['case']}")
        print(f"  Followed by: {r['followed_by']}")
        print(f"  Doubted by:  {r['doubted_by']}")
        print()

    print("=== STUB NODES WITH MULTIPLE CONFLICTING TREATMENTS ===")
    rows = s.run("""
        MATCH (b:Case {in_corpus: false})<-[t:TREATED_BY]-(:Case)
        WITH b, collect(DISTINCT t.treatment_type) AS types
        WHERE size(types) > 1
        RETURN b.case_name AS case, types
    """).data()
    print(f"Found: {len(rows)}")
    for r in rows:
        print(f"  Case: {r['case']}")
        print(f"  Types: {r['types']}")
        print()

driver.close()