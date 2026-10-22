from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

total_violations = 0

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
    total_violations += len(rows)

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
    total_violations += len(rows)

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
    total_violations += len(rows)

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
    total_violations += len(rows)

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
    total_violations += len(rows)

    print()
    print("=== RULE 6: SELF-CITATION ===")
    print("Case treating itself — logically impossible")
    rows = s.run("""
        MATCH (a:Case)-[t:TREATED_BY]->(a)
        RETURN a.doc_id AS case_id, t.treatment_type AS treatment
    """).data()
    print(f"  Violations found: {len(rows)}")
    for r in rows:
        print(f"  {r['case_id']} treats itself as {r['treatment']}")
    total_violations += len(rows)

    print()
    print("=== RULE 7: POST-OVERRULING FOLLOW ===")
    print("Case followed AFTER it was overruled by any court")
    rows = s.run("""
        MATCH (overruler:Case)-[o:TREATED_BY {treatment_type:'overruled'}]->(target:Case)
        MATCH (follower:Case)-[f:TREATED_BY {treatment_type:'followed'}]->(target)
        WHERE f.effective_date > o.effective_date
          AND follower <> overruler
        RETURN target.case_num AS target,
               target.doc_id AS target_id,
               overruler.doc_id AS overruled_by,
               o.effective_date AS overruled_on,
               follower.doc_id AS followed_by,
               f.effective_date AS followed_on
    """).data()
    print(f"  Violations found: {len(rows)}")
    for r in rows:
        print(f"  {r['target']} overruled on {r['overruled_on']}"
              f" but followed by {r['followed_by'][:40]} on {r['followed_on']}")
    total_violations += len(rows)

    print()
    print("=== RULE 8: DUPLICATE TREATMENT EDGES ===")
    print("Same case pair with same treatment type appearing more than once")
    rows = s.run("""
        MATCH (a:Case)-[t:TREATED_BY]->(b:Case)
        WITH a, b, t.treatment_type AS tp, count(*) AS cnt
        WHERE cnt > 1
        RETURN a.doc_id AS treating,
               b.case_name AS cited,
               tp AS treatment_type,
               cnt AS edge_count
        ORDER BY cnt DESC
    """).data()
    print(f"  Violations found: {len(rows)}")
    for r in rows:
        print(f"  {r['treating'][:40]} → {str(r['cited'])[:40]}"
              f" [{r['treatment_type']}] x{r['edge_count']}")
    total_violations += len(rows)

    print()
    print("=== RULE 9: ORPHAN CASE NODES ===")
    print("Case nodes with no edges at all — failed ingestion or extraction")
    rows = s.run("""
        MATCH (c:Case)
        WHERE NOT (c)-[]-() 
        RETURN c.doc_id AS case_id, c.court AS court
        LIMIT 20
    """).data()
    total_orphans = s.run("""
        MATCH (c:Case)
        WHERE NOT (c)-[]-()
        RETURN count(c) AS cnt
    """).single()["cnt"]
    print(f"  Violations found: {total_orphans}")
    for r in rows[:5]:
        print(f"  {r['case_id']} ({r['court']})")
    if total_orphans > 5:
        print(f"  ... and {total_orphans - 5} more")
    total_violations += total_orphans

    print()
    print("=== RULE 10: MISSING DECIDED_BY EDGES ===")
    print("Corpus cases with no judge edges — judge extraction failed")
    rows = s.run("""
        MATCH (c:Case)
        WHERE c.is_stub = false
          AND NOT (c)-[:DECIDED_BY]->()
        RETURN count(c) AS cnt
    """).single()
    missing_judges = rows["cnt"] if rows else 0
    print(f"  Cases with no judge edges: {missing_judges}")
    if missing_judges > 0:
        samples = s.run("""
            MATCH (c:Case)
            WHERE c.is_stub = false
              AND NOT (c)-[:DECIDED_BY]->()
            RETURN c.doc_id AS case_id
            LIMIT 5
        """).data()
        for r in samples:
            print(f"  {r['case_id']}")
    total_violations += missing_judges

    print()
    print("=" * 50)
    print(f"TOTAL VIOLATIONS FOUND: {total_violations}")
    if total_violations == 0:
        print("Graph integrity: CLEAN")
    elif total_violations < 10:
        print("Graph integrity: MINOR ISSUES")
    else:
        print("Graph integrity: REQUIRES ATTENTION")
    print("=" * 50)

driver.close()