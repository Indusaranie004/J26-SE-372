"""
Evaluate graph traversal (expand stage) against GT2.

Metric: Triplet Recall per relationship category, per seed
    recall = |GT2 triplets found by expand()| / |GT2 triplets|
    - a GT2 triplet is found if expand() returns ANY of its matched_ids
    - match on (seed, node) only;
    - scores are macro-averaged over seeds, per category and overall
    - micro recall (all triplets pooled) is reported alongside

Seeds are given directly (oracle seeds), so the score measures traversal only,
not seed retrieval errors.

Usage (from component-b root):
  GT2_PATH=data/gt2_expert.json python3 tests/run_traversal_eval.py
Outputs: evidence/graph_traversal/ (results JSON, CSV, PNG table)
"""
import argparse
import csv
import datetime
import os
import json
import sys
from statistics import mean

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CLEAN_PATH  = os.getenv("GT2_PATH", "data/gt2_expert.json")
OUT_DIR     = "evidence/graph_traversal"
RESULT_PATH = os.path.join(OUT_DIR, "gt2_results.json")
CATEGORIES  = ["judicial_treatment", "legislative_foundation", "litigation_history"]
LABELS      = {"judicial_treatment": "Judicial Treatment",
               "legislative_foundation": "Legislative Foundation",
               "litigation_history": "Litigation History"}


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
            "missed": sorted(t["matched_ids"][0] for t in gt if t not in hits),
        }
    return out


def aggregate(per_seed: list) -> dict:
    summary = {}
    for cat in CATEGORIES:
        sc = [s["scores"][cat] for s in per_seed if cat in s["scores"]]
        found, total = sum(x["found"] for x in sc), sum(x["total"] for x in sc)
        summary[cat] = {"macro_recall": round(mean(x["recall"] for x in sc), 4) if sc else None,
                        "micro_recall": round(found / total, 4) if total else None,
                        "seeds": len(sc), "found": found, "triplets": total}
    allsc = [s["scores"][c] for s in per_seed for c in s["scores"]]
    found, total = sum(x["found"] for x in allsc), sum(x["total"] for x in allsc)
    summary["overall"] = {"macro_recall": round(mean(x["recall"] for x in allsc), 4) if allsc else None,
                          "micro_recall": round(found / total, 4) if total else None,
                          "seeds": len({s["seed_id"] for s in per_seed if s["scores"]}),
                          "found": found, "triplets": total}
    return summary


def save_tables(summary: dict, n_seeds: int, split: str):
    rows = [(LABELS[c], summary[c]) for c in CATEGORIES] + [("Overall", summary["overall"])]
    with open(os.path.join(OUT_DIR, "traversal_table.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Category", "Seeds", "Triplets found / total", "Micro recall", "Macro recall"])
        for name, s in rows:
            w.writerow([name, s["seeds"], f"{s['found']}/{s['triplets']}", s["micro_recall"], s["macro_recall"]])
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed -> CSV saved, PNG skipped"); return

    NAVY, GRID = "#1F3864", "#BFBFBF"
    fmt = lambda v: "-" if v is None else f"{v:.2f}"
    cells = [[name, str(s["seeds"]), f"{s['found']} / {s['triplets']}", fmt(s["micro_recall"]), fmt(s["macro_recall"])]
             for name, s in rows]
    fig, ax = plt.subplots(figsize=(10, 0.6 + 0.36 * len(cells))); ax.axis("off")
    t = ax.table(cellText=cells, colLabels=["Relationship category", "Seeds", "Triplets found / total",
                                            "Micro recall", "Macro recall"],
                 colWidths=[0.34, 0.10, 0.22, 0.16, 0.16], loc="upper center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(10); t.scale(1, 1.6)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor(GRID)
        if r == 0:
            cell.set_facecolor(NAVY); cell.set_text_props(color="white", weight="bold"); continue
        if c == 0: cell.set_text_props(ha="left"); cell._loc = "left"
        if r == len(cells): cell.set_text_props(weight="bold"); cell.set_facecolor("#E2F0D9")
    ax.set_title(f"Expand Stage: Triplet Recall (oracle seeds)  |  split: {split}  |  {n_seeds} expert-validated seeds ({summary['overall']['seeds']} with links)",
                 fontsize=12, weight="bold", loc="left", pad=6)
    ax.text(0, -0.02, f"GT: {CLEAN_PATH}  |  run: {datetime.datetime.now():%Y-%m-%d %H:%M}  |  "
                      "micro = all triplets pooled; macro = mean over seeds",
            fontsize=8, color="#555555", transform=ax.transAxes, va="top")
    fig.savefig(os.path.join(OUT_DIR, "traversal_table.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    from retrieval.expand.traversal import expand

    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "eval", "all"], default="all")
    args = ap.parse_args()

    gt2 = json.load(open(CLEAN_PATH, encoding="utf-8"))
    if args.split != "all":
        gt2 = [e for e in gt2 if e.get("split") in (args.split, "both")]

    per_seed = []
    for entry in sorted(gt2, key=lambda e: e["seed_id"]):
        cluster = expand([entry["seed_id"]])[0]
        per_seed.append({"seed_id": entry["seed_id"],
                         "scores": score_seed(entry, returned_ids(cluster))})

    summary = aggregate(per_seed)
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump({"gt2_path": CLEAN_PATH, "split": args.split, "summary": summary, "per_seed": per_seed},
              open(RESULT_PATH, "w", encoding="utf-8"), indent=2)
    save_tables(summary, len(gt2), args.split)

    print(f"GT2 Triplet Recall  (split={args.split}, seeds={len(gt2)}, GT={CLEAN_PATH})")
    for cat in CATEGORIES + ["overall"]:
        s = summary[cat]
        print(f"  {cat:<24} micro={s['micro_recall']}  macro={s['macro_recall']}  "
              f"({s['found']}/{s['triplets']} triplets, {s['seeds']} seeds)")
    print(f"\nSaved results JSON, CSV and PNG in {OUT_DIR}/")


if __name__ == "__main__":
    main()

#GT2_PATH=data/gt2_expert.json python3 tests/run_traversal_eval.py