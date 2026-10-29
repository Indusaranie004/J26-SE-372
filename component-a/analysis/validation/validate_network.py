from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

with driver.session() as s:

    print("=== TREATMENT TYPE DISTRIBUTION ===")
    rows = s.run("""
        MATCH ()-[t:TREATED_BY]->()
        RETURN t.treatment_type AS type, count(t) AS count
        ORDER BY count DESC
    """).data()
    for r in rows:
        print(f"  {r['type']:<20} {r['count']}")

    print("\n=== MOST CITED CASES ===")
    rows = s.run("""
        MATCH (a:Case)-[:TREATED_BY]->(b:Case)
        RETURN b.case_name AS case, count(a) AS times_cited
        ORDER BY times_cited DESC LIMIT 10
    """).data()
    for r in rows:
        name = (r['case'] or 'unknown')[:50]
        print(f"  {name:<50} cited {r['times_cited']} times")

    print("\n=== IN CORPUS vs STUBS ===")
    rows = s.run("""
        MATCH (c:Case)
        RETURN c.in_corpus AS in_corpus, count(c) AS count
    """).data()
    for r in rows:
        label = "Real cases" if r['in_corpus'] else "Stub nodes"
        print(f"  {label}: {r['count']}")

    print("\n=== CITATION DENSITY ===")
    rows = s.run("""
        MATCH (a:Case)-[t:TREATED_BY]->()
        WHERE a.in_corpus = true
        RETURN count(DISTINCT a) AS docs_with_edges,
               count(t) AS total_edges
    """).data()
    r = rows[0]
    density = r['total_edges'] / r['docs_with_edges'] if r['docs_with_edges'] else 0
    print(f"  Documents with treatment edges: {r['docs_with_edges']}")
    print(f"  Total treatment edges: {r['total_edges']}")
    print(f"  Average edges per document: {density:.1f}")

    print("\n=== VALIDITY STATUS DISTRIBUTION ===")
    rows = s.run("""
        MATCH (c:Case)
        RETURN coalesce(c.validity_status, 'unknown') AS status, 
            count(c) AS count
        ORDER BY count DESC
    """).data()
    for r in rows:
        print(f"  {r['status']:<30} {r['count']}")

    print("\n=== GRAPH SUMMARY ===")
    for label in ['Case', 'Judge', 'Act']:
        count = s.run(
            f"MATCH (n:{label}) RETURN count(n) AS c"
        ).single()['c']
        print(f"  {label} nodes: {count}")
    for rel in ['TREATED_BY', 'DECIDED_BY', 'INVOLVES_ACT']:
        count = s.run(
            f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c"
        ).single()['c']
        print(f"  {rel} edges: {count}")

driver.close()