"""

Generates training triplets for BGE-M3 and AnglE-BERT fine-tuning (Stage 1).
Each triplet: (query, positive_doc_body, hard_negative_body)
- Positive: body text of the relevant case(s) for the query
- Hard negative: top BM25 match that is NOT a relevant case


"""

import json
import re
from rank_bm25 import BM25Okapi  

#Paths
CASES_PATH   = "data/all_cases.json"
GT1_PATH     = "data/gt1_queries.json"
OUTPUT_PATH  = "data/triplets.json"

#Load Data
with open(CASES_PATH) as f:
    cases = json.load(f)["cases"]

with open(GT1_PATH) as f:
    gt1 = json.load(f)

#Build doc index
doc_by_id = {c["doc_id"]: c for c in cases}

def get_body(doc_id: str) -> str:
    c = doc_by_id.get(doc_id)
    if not c:
        return ""
    return c["sections"]["body"]["text"].strip()

#Build BM25 corpus over all 190 cases
def tokenize(text: str):
    return re.findall(r"\w+", text.lower())

corpus_ids   = [c["doc_id"] for c in cases]
corpus_texts = [get_body(c["doc_id"]) for c in cases]
tokenized    = [tokenize(t) for t in corpus_texts]
bm25         = BM25Okapi(tokenized)

#Generate triplets (train split only)
train_queries = [q for q in gt1 if q["split"] == "train"]

triplets = []
skipped  = 0

for q in train_queries:
    query_text   = q["query"]
    relevant_ids = set(q["relevant_ids"])

    #Positive: use body of first relevant doc
    pos_id   = q["relevant_ids"][0]
    pos_body = get_body(pos_id)
    if not pos_body:
        print(f"SKIPPED: {query_text} | pos_id: {pos_id}")
        skipped += 1
        continue

    #Hard negative: BM25 top-k, pick first that is not relevant
    scores   = bm25.get_scores(tokenize(query_text))
    ranked   = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    neg_body = None
    neg_id   = None
    for idx in ranked:
        candidate_id = corpus_ids[idx]
        if candidate_id not in relevant_ids:
            neg_body = corpus_texts[idx]
            neg_id   = candidate_id
            break

    if not neg_body:
        skipped += 1
        continue

    triplets.append({
        "query":          query_text,
        "positive":       pos_body,
        "negative":       neg_body,
        "positive_id":    pos_id,
        "negative_id":    neg_id,
        "intent":         q["intent"]
    })

#Save
with open(OUTPUT_PATH, "w") as f:
    json.dump(triplets, f, indent=2, ensure_ascii=False)

print(f"Triplets generated : {len(triplets)}")
print(f"Skipped            : {skipped}")
print(f"Saved to           : {OUTPUT_PATH}")