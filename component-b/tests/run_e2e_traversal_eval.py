"""
End-to-end legal context completeness: triplet recall with retrieved seeds.

For each expert-validated GT1 query:
  expected  = GT2 triplets of the query's relevant case(s)      (data/gt2_expert.json)
  seeds     = top-K cases from a seed retriever (ablation rows)
  returned  = union of expand() output over those K seeds, per category
  recall    = expected triplets found / expected triplets       (same rule as run_traversal_eval.py)

Traversal is identical for every row; only the seed retriever changes.
Oracle row = the relevant case(s) given directly (upper bound).
Aggregation: macro over queries (per category and overall), micro = all triplets pooled.

Usage (from component-b root):
  GT1_PATH=data/gt1_expert.json GT2_PATH=data/gt2_expert.json python3 tests/run_e2e_traversal_eval.py
  options: --split eval|all (default eval)   --k 5
Outputs: evidence/graph_traversal/ (e2e_traversal_results.json, e2e_traversal_table.csv/.png)
"""
import argparse, csv, datetime, json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import (COLLECTION_GENERIC, COLLECTION_BGEM3_FINETUNED,
                    COLLECTION_ANGLEBERT_FINETUNED, ANGLEBERT_CKPT, BGE_FT_CKPT, RRF_K)
from retrieval.seed.bm25_retriever import BM25Retriever
from retrieval.seed.dense_retriever import DenseRetriever
from retrieval.seed.hybrid import retrieve_concurrent, rrf_merge
from retrieval.expand.traversal import expand
from tests.run_traversal_eval import score_seed, returned_ids, aggregate, CATEGORIES, LABELS

GT1_PATH   = os.getenv("GT1_PATH", "data/gt1_expert.json")
GT2_PATH   = os.getenv("GT2_PATH", "data/gt2_expert.json")
CASES_PATH = os.getenv("CASES_PATH", "data/all_cases.json")
OUT_DIR    = "evidence/graph_traversal"
DEPTH      = 100
BASELINE   = "4  Hybrid, generic BGE-M3 + RRF [Arulanandam & De Silva]"
PROPOSED   = "5  Hybrid, BGE-M3 (FT) + RRF [PROPOSED]"
ORACLE     = "Oracle seeds (upper bound)"

ap = argparse.ArgumentParser()
ap.add_argument("--split", choices=["eval", "all"], default="eval")
ap.add_argument("--k", type=int, default=5)
args = ap.parse_args()
K = args.k

# ── Ground truth ─────────────────────────────────────────────────────────────
gt1 = json.load(open(GT1_PATH, encoding="utf-8"))
if args.split == "eval":
    gt1 = [g for g in gt1 if g.get("split") in ("eval", "both")]
gt2 = {e["seed_id"]: e for e in json.load(open(GT2_PATH, encoding="utf-8"))}

def expected_for(g):
    """GT2 triplets of the query's relevant case(s), per category."""
    return {c: [t for s in g["relevant_ids"] if s in gt2 for t in gt2[s]["expected"].get(c, [])]
            for c in CATEGORIES}

# ── Retrievers (same construction as tests/run_ablation.py) ──────────────────
def build_text(sections):
    parts = []
    for key in ("caption", "header", "body", "conclusion"):
        val = sections.get(key) or {}
        val = val.get("text", "") if isinstance(val, dict) else val
        if val:
            parts.append(val.strip())
    return "\n\n".join(parts)

cases = json.load(open(CASES_PATH, encoding="utf-8"))["cases"]
dense_corpus = [{"id": c["doc_id"], "text": build_text(c["sections"])}
                for c in cases if c.get("sections") and build_text(c["sections"])]
if os.getenv("CORPUS_SOURCE", "local") == "api":
    from api.corpus_loader import fetch_corpus_from_api
    bm25_corpus = fetch_corpus_from_api()
else:
    bm25_corpus = [{"id": c["doc_id"], "text": c["sections"]["body"]["text"]}
                   for c in cases if (c.get("sections") or {}).get("body", {}).get("text")]

def dense(mode, collection, ckpt=None):
    r = DenseRetriever(mode=mode, collection_name=collection, checkpoint_path=ckpt)
    if r.collection.count() != len(dense_corpus):
        r.index_corpus(dense_corpus)
    return r

bm25      = BM25Retriever(bm25_corpus)
dense_gen = dense("generic", COLLECTION_GENERIC)
dense_bge = dense("finetuned", COLLECTION_BGEM3_FINETUNED, BGE_FT_CKPT) if BGE_FT_CKPT else None
dense_ang = dense("finetuned", COLLECTION_ANGLEBERT_FINETUNED, ANGLEBERT_CKPT) if ANGLEBERT_CKPT else None

hybrid = lambda d: (lambda q: rrf_merge(*retrieve_concurrent(q, bm25, d, DEPTH), k=RRF_K))
ROWS = {"1  Sparse-only (BM25) [Luan et al.]": lambda q: bm25.search(q, DEPTH)}
if dense_ang: ROWS["3a Dense-only, AnglE-BERT (FT) [Jayawardena et al.]"] = lambda q: dense_ang.search(q, DEPTH)
ROWS[BASELINE] = hybrid(dense_gen)
if dense_ang: ROWS["5b Hybrid, AnglE-BERT (FT) + RRF [supplementary]"] = hybrid(dense_ang)
if dense_bge: ROWS[PROPOSED] = hybrid(dense_bge)
ROWS[ORACLE] = None

# ── Traversal (cached per seed; identical for every row) ─────────────────────
_cache = {}
def returned_for(seed_ids):
    got = {c: set() for c in CATEGORIES}
    for sid in seed_ids:
        if sid not in _cache:
            _cache[sid] = returned_ids(expand([sid])[0])
        for c in CATEGORIES:
            got[c] |= _cache[sid][c]
    return got

# ── Scoring ──────────────────────────────────────────────────────────────────
results = {"gt1_path": GT1_PATH, "gt2_path": GT2_PATH, "split": args.split, "k": K,
           "n_queries": len(gt1), "rows": {}}
for name, retrieve in ROWS.items():
    per_q = []
    for g in sorted(gt1, key=lambda x: x["query"]):
        seeds = list(g["relevant_ids"]) if retrieve is None else [d for d, _ in retrieve(g["query"])[:K]]
        per_q.append({"seed_id": g["query"], "seeds": seeds,
                      "scores": score_seed({"expected": expected_for(g)}, returned_for(seeds))})
    results["rows"][name] = {"summary": aggregate(per_q), "per_query": per_q}

os.makedirs(OUT_DIR, exist_ok=True)
json.dump(results, open(os.path.join(OUT_DIR, "e2e_traversal_results.json"), "w", encoding="utf-8"), indent=2)

# ── Print ────────────────────────────────────────────────────────────────────
S = {n: r["summary"] for n, r in results["rows"].items()}
cols = ["Judicial", "Legislation", "Litigation"] + ["Overall micro", "Overall macro"]
def vals(s):
    return [s[c]["macro_recall"] for c in CATEGORIES] + [s["overall"]["micro_recall"], s["overall"]["macro_recall"]]

n_with = S[ORACLE]["overall"]["seeds"]
print(f"\nEnd-to-end triplet recall  (split={args.split}, top-{K} seeds, {len(gt1)} queries, {n_with} with links)")
print(f"{'':62}" + "".join(f"{c.split()[0][:11]:>12}" for c in cols))
for name in ROWS:
    print(f"{name:62}" + "".join(f"{'-' if v is None else f'{v:.4f}':>12}" for v in vals(S[name])))
delta = None
if PROPOSED in S:
    delta = [S[PROPOSED]["overall"]["micro_recall"] - S[BASELINE]["overall"]["micro_recall"],
             S[PROPOSED]["overall"]["macro_recall"] - S[BASELINE]["overall"]["macro_recall"]]
    print(f"\nΔ vs baseline (Row 5 − Row 4): overall micro {delta[0]:+.4f}  overall macro {delta[1]:+.4f}")

# ── Evidence tables (CSV + PNG) ──────────────────────────────────────────────
with open(os.path.join(OUT_DIR, "e2e_traversal_table.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Seed retriever"] + cols)
    for name in ROWS: w.writerow([name] + vals(S[name]))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print(f"matplotlib not installed -> CSV saved, PNG skipped"); sys.exit(0)

NAVY, PROP, BASE, GRID = "#1F3864", "#E2F0D9", "#FFF2CC", "#BFBFBF"
fmt = lambda v: "-" if v is None else f"{v:.2f}"
names = list(ROWS)
label = lambda n: n + ("  (baseline)" if n == BASELINE else "")
cells = [[label(n)] + [fmt(v) for v in vals(S[n])] for n in names]
fig, ax = plt.subplots(figsize=(14, 0.8 + 0.36 * len(cells))); ax.axis("off")
t = ax.table(cellText=cells, colLabels=["Seed retriever"] + cols,
             colWidths=[0.44] + [0.112] * len(cols), loc="upper center", cellLoc="center")
t.auto_set_font_size(False); t.set_fontsize(10); t.scale(1, 1.6)
for (r, c), cell in t.get_celld().items():
    cell.set_edgecolor(GRID)
    if r == 0:
        cell.set_facecolor(NAVY); cell.set_text_props(color="white", weight="bold"); continue
    if c == 0: cell.set_text_props(ha="left"); cell._loc = "left"
    n = names[r - 1]
    if n == PROPOSED: cell.set_facecolor(PROP); cell.set_text_props(weight="bold")
    if n == BASELINE: cell.set_facecolor(BASE)
    if n == ORACLE:   cell.set_text_props(color="#555555", style="italic")
ax.set_title(f"Legal Context Completeness (end-to-end): Triplet Recall with top-{K} retrieved seeds  |  "
             f"split: {args.split}  |  {len(gt1)} queries ({n_with} with links)",
             fontsize=12, weight="bold", loc="left", pad=6)
foot = (f"GT: {GT1_PATH} + {GT2_PATH}  |  run: {datetime.datetime.now():%Y-%m-%d %H:%M}  |  "
        "traversal identical for every row  |  category columns = macro over queries")
if delta:
    foot += f"\nΔ vs baseline (Row 5 − Row 4): overall micro {delta[0]:+.2f}, overall macro {delta[1]:+.2f}"
ax.text(0, -0.02, foot, fontsize=8, color="#555555", transform=ax.transAxes, va="top")
fig.savefig(os.path.join(OUT_DIR, "e2e_traversal_table.png"), dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"\nSaved results JSON, CSV and PNG in {OUT_DIR}/")

#GT1_PATH=data/gt1_expert.json GT2_PATH=data/gt2_expert.json python3 tests/run_e2e_traversal_eval.py