import json, glob, re

# Broader keyword list — catch more candidates for manual review
TREATMENT_KW = [
    "followed", "distinguished", "overruled", "doubted",
    "per incuriam", "no longer good law", "applied", "approved",
    "could be distinguished", "is distinguishable",
    "adopted", "affirmed", "endorsed", "relied on",
    "not followed", "decline to follow", "wrongly decided",
    "questioned", "called into doubt", "does not apply",
    "inapplicable", "confined to", "considered and applied",
    "cited with approval", "approved of"
]

CITATION_RX = re.compile(
    r'[A-Z][A-Za-z.\-\']+(?:\s+[A-Z][A-Za-z.\-\']+){0,4}'
    r'\s+[Vv]s?\.?\s+[A-Z][A-Za-z.\-\']+',
)

tasks = []
seen = set()

for path in glob.glob("corpus/cases/*.json"):
    rec  = json.load(open(path, encoding="utf-8"))
    body = rec["sections"].get("body", {}).get("text", "")
    doc_id = rec["doc_id"]

    # Use larger window — 3 sentences together
    sentences = re.split(r'(?<=[.!?])\s+', body)

    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) < 30 or len(sent) > 800:
            continue
        if sent in seen:
            continue
        if any(k in sent.lower() for k in TREATMENT_KW):
            if CITATION_RX.search(sent):
                seen.add(sent)
                tasks.append({
                    "id":     f"{doc_id}_{i}",
                    "doc_id": doc_id,
                    "text":   sent,
                    "label":  "",
                    "cited":  "",
                    "notes":  ""
                })

print(f"Found {len(tasks)} candidate sentences for annotation")

import csv
with open("analysis/annotation_candidates.json", "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

with open("analysis/annotation_candidates.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id","doc_id","text","label","cited","notes"])
    writer.writeheader()
    writer.writerows(tasks)

print("Saved to analysis/annotation_candidates.csv")
print("Label options: followed / distinguished / overruled / doubted / none")