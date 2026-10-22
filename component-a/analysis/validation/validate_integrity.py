from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

with driver.session() as s:

    print("=== RULE 1: TEMPORAL INCONSISTENCY ===")
    print("Case followed AFTER the date it was overruled")
    rows = s.run("""
        MATCH (a:Case)-[f:TREATED_BY {treatment_type:'followed'}]->(target:Case)
        MATCH (b:Case)-[o:TREATED_BY {treatment_type:'overruled'}]->(target)
        WHERE f.effective_date > o.effective_date
        RETURN target.case_num AS target,
               f.effective_date AS followed_on,
               o.effective_date AS overruled_on
    """).data()
    print(f"  Violations found: {len(rows)}")
    for r in rows:
        print(f"  {r['target']} — followed {r['followed_on']} after overruled {r['overruled_on']}")

    print()
    print("=== RULE 2: HIERARCHY INCONSISTENCY ===")
    print("Lower court overruling a higher court — legally impossible")
    rows = s.run("""
        MATCH (lower:Case)-[t:TREATED_BY {treatment_type:'overruled'}]->(higher:Case)
        WHERE (lower.court = 'CA' AND higher.court = 'SC')
           OR (lower.court = 'DC' AND higher.court IN ['SC','CA'])
           OR (lower.court = 'HC' AND higher.court = 'SC')
        RETURN lower.doc_id AS lower_case,
               lower.court  AS lower_court,
               higher.doc_id AS higher_case,
               higher.court  AS higher_court,
               t.evidence    AS evidence
    """).data()
    print(f"  Violations found: {len(rows)}")
    for r in rows:
        print(f"  {r['lower_court']} overruling {r['higher_court']}")
        print(f"  Evidence: {str(r['evidence'])[:100]}")

    print()
    print("=== RULE 3: CONFLICTING TREATMENT ===")
    print("Two cases treating same ancestor in opposing directions")
    rows = s.run("""
        MATCH (a:Case)-[t1:TREATED_BY]->(anc:Case)<-[t2:TREATED_BY]-(b:Case)
        WHERE t1.treatment_type IN ['followed','approved']
          AND t2.treatment_type IN ['overruled','not_followed']
          AND a <> b
        RETURN anc.case_num AS ancestor,
               a.doc_id AS follower,
               t1.treatment_type AS t1_type,
               b.doc_id AS overruler,
               t2.treatment_type AS t2_type
    """).data()
    print(f"  Violations found: {len(rows)}")
    for r in rows:
        print(f"  {r['ancestor']}: followed by {r['follower'][:30]} "
              f"but {r['t2_type']} by {r['overruler'][:30]}")

    print()
    print("=== RULE 4: CYCLIC TREATMENT ===")
    print("Case A overrules Case B which overrules Case A")
    rows = s.run("""
        MATCH (a:Case)-[:TREATED_BY]->(b:Case)-[:TREATED_BY]->(a)
        RETURN a.doc_id AS case_a, b.doc_id AS case_b
    """).data()
    print(f"  Violations found: {len(rows)}")
    for r in rows:
        print(f"  {r['case_a']} ↔ {r['case_b']}")

    print()
    print("=== RULE 5: STATE INCONSISTENCY ===")
    print("Case marked good_law but has incoming overruled edge")
    rows = s.run("""
        MATCH (c:Case {validity_status:'good_law'})
              <-[t:TREATED_BY {treatment_type:'overruled'}]-(:Case)
        RETURN c.doc_id AS case_id,
               c.case_num AS case_num,
               t.evidence AS evidence
    """).data()
    print(f"  Violations found: {len(rows)}")
    for r in rows:
        print(f"  {r['case_num']}: marked good_law but has overruled edge")
        print(f"  Evidence: {str(r['evidence'])[:100]}")

    print()
    print("=== SUMMARY ===")

driver.close()