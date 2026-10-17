from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

with driver.session() as s:
    print("NODES:")
    nodes = s.run(
        "MATCH (n) RETURN labels(n)[0] AS l, count(n) AS c ORDER BY c DESC"
    ).data()
    for n in nodes:
        print(f"  {n['l']}: {n['c']}")

    print()
    print("RELATIONSHIPS:")
    rels = s.run(
        "MATCH ()-[r]->() RETURN type(r) AS t, count(r) AS c ORDER BY c DESC"
    ).data()
    for r in rels:
        print(f"  {r['t']}: {r['c']}")

    print()
    print("APPEALED_FROM sample:")
    rows = s.run("""
        MATCH (sc:Case {court:'SC'})-[:APPEALED_FROM]->(lower:Case)
        RETURN sc.doc_id AS sc_case, lower.court AS lower_court,
               lower.num AS lower_num
        LIMIT 5
    """).data()
    for r in rows:
        print(f"  {r['sc_case'][:40]} -> {r['lower_court']} {r['lower_num']}")

driver.close()