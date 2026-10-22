import json, glob, re

# Known overruled cases to search for
SEARCH_TERMS = [
    ("Ramachandran", "Sunpac", "parate execution"),
    ("Gunawardane", "Muthukumarana", "jurisdiction"),
    ("Pathirathne", "Abeywardena", "constitutional council"),
    ("Walker Sons", "Gunatilake", "labour"),
    ("Bandaranayake", "impeachment", "parliament"),
    ("FR 351", "dissolution", "parliament"),
]

results = []

for path in glob.glob("corpus/cases/*.json"):
    rec  = json.load(open(path, encoding="utf-8"))
    body = rec["sections"].get("body", {}).get("text", "")
    doc_id = rec["doc_id"]

    for terms in SEARCH_TERMS:
        # Check if at least 2 of the 3 terms appear in the document
        matches = sum(1 for t in terms if t.lower() in body.lower())
        if matches >= 2:
            # Find the relevant sentence
            for term in terms:
                idx = body.lower().find(term.lower())
                if idx != -1:
                    snippet = body[max(0,idx-200):idx+300].strip()
                    # Check for overruling language nearby
                    overrul_kw = ["overrul", "per incuriam", "no longer",
                                  "wrongly", "unable to agree", "fell into error",
                                  "expressly overrul", "explicitly overrul"]
                    if any(k in snippet.lower() for k in overrul_kw):
                        results.append({
                            "doc_id":  doc_id,
                            "terms":   terms,
                            "snippet": snippet[:400]
                        })
                        break

print(f"Found {len(results)} matches")
print()
for r in results:
    print(f"DOC: {r['doc_id']}")
    print(f"TERMS: {r['terms']}")
    print(f"SNIPPET: {r['snippet'][:300]}")
    print()