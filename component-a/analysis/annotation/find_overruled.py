import json, glob, re, csv

OVERRULED_RX = re.compile(
    r'(?:'
    r'must be overruled|'
    r'is hereby overruled|'
    r'are hereby overruled|'
    r'was wrongly decided|'
    r'were wrongly decided|'
    r'overruling\s+[A-Z]|'
    r'I overrule|'
    r'we overrule|'
    r'court overrules|'
    r'no longer good law|'
    r'not good law|'
    r'bad law|'
    r'cannot be regarded as good law|'
    r'should not be followed|'
    r'ought not to be followed|'
    r'decline to follow|'
    r'declined to follow|'
    r'unable to agree with the (?:view|decision|judgment|reasoning)|'
    r'fell into (?:error|a serious error)|'
    r'with respect.*?(?:cannot|disagree|wrong)|'
    r'per incuriam.*?overrul|'
    r'expressly overrul'
    r')',
    re.IGNORECASE
)

CITATION_RX = re.compile(
    r'[A-Z][A-Za-z.\-\']+(?:\s+[A-Z][A-Za-z.\-\']+){0,4}'
    r'\s+[Vv]s?\.?\s+[A-Z][A-Za-z.\-\']+',
)

results = []
seen = set()

for path in glob.glob("corpus/cases/*.json"):
    rec  = json.load(open(path, encoding="utf-8"))
    body = rec["sections"].get("body", {}).get("text", "")
    doc_id = rec["doc_id"]

    sentences = re.split(r'(?<=[.!?])\s+', body)

    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) < 30 or len(sent) > 800:
            continue
        if sent in seen:
            continue
        if OVERRULED_RX.search(sent) and CITATION_RX.search(sent):
            seen.add(sent)
            results.append({
                "id":     f"{doc_id}_{i}",
                "doc_id": doc_id,
                "text":   sent,
                "label":  "",
            })

print(f"Found {len(results)} candidate overruled sentences")
print()
for r in results:
    print(f"ID: {r['id']}")
    print(f"TEXT: {r['text']}")
    print()

with open("analysis/overruled_candidates.csv", "w",
          newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f,
             fieldnames=["id","doc_id","text","label"])
    writer.writeheader()
    writer.writerows(results)

print(f"Saved {len(results)} to analysis/overruled_candidates.csv")