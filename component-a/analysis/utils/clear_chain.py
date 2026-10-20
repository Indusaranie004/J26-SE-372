from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

with driver.session() as s:
    s.run("MATCH ()-[r:APPEALED_FROM]->() DELETE r")
    print("APPEALED_FROM edges deleted")

    s.run("""
        MATCH (n:Case)
        WHERE n.court IN ['CA','DC','HC']
        AND n.in_corpus = false
        DELETE n
    """)
    print("Lower court stub nodes deleted")

    count = s.run(
        "MATCH ()-[r:APPEALED_FROM]->() RETURN count(r) AS c"
    ).single()["c"]
    print(f"APPEALED_FROM remaining: {count}")

driver.close()