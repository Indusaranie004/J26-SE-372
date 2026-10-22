from dotenv import load_dotenv
import os, json
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

LABEL2ID = {
    "followed":      0,
    "distinguished": 1,
    "overruled":     2,
    "doubted":       3
}

with driver.session() as s:
    rows = s.run("""
        MATCH (a:Case)-[t:TREATED_BY]->(b:Case)
        WHERE t.evidence IS NOT NULL
          AND t.treatment_type IN ['followed','distinguished','overruled','doubted']
        RETURN a.doc_id        AS treating_doc,
               a.case_num      AS treating_num,
               b.case_name     AS cited_name,
               t.treatment_type AS label,
               t.evidence       AS evidence,
               t.effective_date AS date
        ORDER BY t.treatment_type
    """).data()

driver.close()

print(f"Total edges with evidence: {len(rows)}")
print()
for label in ["followed","distinguished","overruled","doubted"]:
    count = len([r for r in rows if r["label"] == label])
    print(f"  {label}: {count}")

dataset = []
for r in rows:
    if not r["evidence"] or len(r["evidence"].strip()) < 20:
        continue
    dataset.append({
        "text":      r["evidence"].strip(),
        "label":     LABEL2ID[r["label"]],
        "label_str": r["label"],
        "doc_id":    r["treating_doc"],
        "cited":     r["cited_name"]
    })

print(f"\nDataset after filtering short evidence: {len(dataset)}")

with open("analysis/training_data.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print("Saved to analysis/training_data.json")
print()
print("Sample entries:")
for item in dataset[:3]:
    print(f"  [{item['label_str']}] {item['text'][:100]}")