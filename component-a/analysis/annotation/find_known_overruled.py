import json, glob

known = [
    "Ameen v Raji",
    "Mohideen v Carder",
    "Mendis v RVDB",
    "Balagalla v Somarathne",
    "Wijesuriya v Siriwardena",
    "Jayawardena v Perera",
    "Fernando v Perera",
    "Hapugoda v Jayasekera",
    "Gunawardena v Perera",
    "Peiris v Perera",
    "Crest Gems v Colombo Municipal",
    "Nordenfelt v Maxim",
    "Jamaldeen v Abdul Majeed",
]

OVERRULED_KW = [
    "overrul", "per incuriam", "no longer good law",
    "wrongly decided", "unable to agree", "fell into error",
    "should not be followed", "decline to follow",
    "cannot be supported", "bad law"
]

found = []

for path in glob.glob("corpus/cases/*.json"):
    rec  = json.load(open(path, encoding="utf-8"))
    body = rec["sections"].get("body", {}).get("text", "")
    doc_id = rec["doc_id"]

    for case in known:
        parts = case.lower().split(" v ")
        if len(parts) != 2:
            continue
        if parts[0] in body.lower() and parts[1] in body.lower():
            idx = body.lower().find(parts[0])
            snippet = body[max(0, idx-150):idx+250]
            if any(kw in snippet.lower() for kw in OVERRULED_KW):
                print(f"CASE:    {case}")
                print(f"DOC:     {doc_id}")
                print(f"SNIPPET: {snippet[:300]}")
                print()
                found.append({"case": case, "doc_id": doc_id,
                              "snippet": snippet[:300]})
                break

print(f"Total found: {len(found)}")