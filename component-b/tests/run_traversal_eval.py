"""
Evaluate graph traversal (expand stage) against GT2.

Metric: Triplet Recall per relationship category, per seed
    recall = |GT2 triplets found by expand()| / |GT2 triplets|
    - a GT2 triplet is found if expand() returns ANY of its matched_ids
    - match on (seed, node) only;
    - scores are macro-averaged over seeds, per category and overall

Seeds are given directly (oracle seeds), so the score measures traversal only,
not seed retrieval errors.

"""
import argparse
import os
import json
import sys
from statistics import mean

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CLEAN_PATH  = "data/gt2_clean.json"
RESULT_PATH = "evidence/gt2_results.json"
CATEGORIES  = ["judicial_treatment", "legislative_foundation", "litigation_history"]


def returned_ids(cluster) -> dict:
    ctx = cluster.legal_context
    return {
        "judicial_treatment":     {e.target_id  for e in ctx.judicial_treatment},
        "legislative_foundation": {e.act_id     for e in ctx.legislative_foundation},
        "litigation_history":     {e.related_id for e in ctx.litigation_history},
    }


def score_seed(entry: dict, got: dict) -> dict:
    out = {}
    for cat in CATEGORIES:
        gt = entry["expected"].get(cat, [])
        if not gt:
            continue
        hits = [t for t in gt if set(t["matched_ids"]) & got[cat]]
        out[cat] = {
            "recall": len(hits) / len(gt),
            "found":  len(hits),
            "total":  len(gt),
            "missed": [t["matched_ids"] for t in gt if t not in hits],
        }
    return out


def aggregate(per_seed: list) -> dict:
    summary = {}
    for cat in CATEGORIES:
        vals = [s["scores"][cat]["recall"] for s in per_seed if cat in s["scores"]]
        n = sum(s["scores"][cat]["total"] for s in per_seed if cat in s["scores"])
        summary[cat] = {"recall": round(mean(vals), 4) if vals else None, "seeds": len(vals), "triplets": n}
    overall = [s["scores"][c]["recall"] for s in per_seed for c in s["scores"]]
    summary["overall_macro"] = round(mean(overall), 4) if overall else None
    return summary


def main():
    from retrieval.expand.traversal import expand

    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "eval", "both", "all"], default="all")
    args = ap.parse_args()

    gt2 = json.load(open(CLEAN_PATH, encoding="utf-8"))
    if args.split != "all":
        gt2 = [e for e in gt2 if e.get("split") in (args.split, "both")]

    per_seed = []
    for entry in gt2:
        cluster = expand([entry["seed_id"]])[0]
        per_seed.append({"seed_id": entry["seed_id"],
                         "scores": score_seed(entry, returned_ids(cluster))})

    summary = aggregate(per_seed)
    os.makedirs("evidence", exist_ok=True)
    json.dump({"split": args.split, "summary": summary, "per_seed": per_seed},
              open(RESULT_PATH, "w", encoding="utf-8"), indent=2)

    print(f"GT2 Triplet Recall  (split={args.split}, seeds={len(gt2)})")
    for cat in CATEGORIES:
        s = summary[cat]
        print(f"  {cat:<24} recall={s['recall']}  (seeds={s['seeds']}, triplets={s['triplets']})")
    print(f"  {'overall (macro)':<24} recall={summary['overall_macro']}")
    print(f"\nPer-seed results: {RESULT_PATH}")


if __name__ == "__main__":
    main()