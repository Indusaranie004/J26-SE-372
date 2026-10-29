"""
Seed Stage ablation study (proposal Table 1) on the expert-validated GT1.

Rows
  1  Sparse-only (BM25)                              baseline: Luan et al. [6]
  2  Dense-only, generic BGE-M3
  3a Dense-only, domain-specific AnglE-BERT (FT)     baseline: Jayawardena et al. [1] (SCaLe-QA replication)
  3b Dense-only, domain-specific BGE-M3 (FT)         isolates the embedding swap
  4  Hybrid, generic BGE-M3 + static RRF            baseline: Arulanandam & De Silva [4]
  5  Hybrid, domain-specific BGE-M3 + static RRF    PROPOSED seed stage (PP1)
  6  Hybrid, domain-specific BGE-M3 + adaptive RRF  PP2 / F1 scope (not run here)

Novelty comparisons printed at the end:
  5 vs 4   effect of domain-specific embeddings inside the hybrid (same fusion)
  5 vs 3b  effect of keeping the sparse leg (same embeddings)
  5 vs 3a  proposed engine vs the SCaLe-QA style domain-specific dense-only baseline

Subsets
  all          every validated query
  eval         queries in the eval split (not used to build fine-tuning triplets)
  eval-unseen  eval queries whose relevant cases never appear in a train query
               (strictest: the fine-tuned models never saw these cases as positives)
Fine-tuned rows (3a, 3b, 5) should be reported on eval / eval-unseen.

Usage (from component-b root):
  GT1_PATH=data/gt1_expert.json ANGLEBERT_CKPT=<path> BGE_FT_CKPT=<path> python tests/run_ablation.py
"""
import json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import (GT1_PATH, COLLECTION_GENERIC, COLLECTION_BGEM3_FINETUNED,
                    COLLECTION_ANGLEBERT_FINETUNED, ANGLEBERT_CKPT, BGE_FT_CKPT, RRF_K)
from retrieval.seed.bm25_retriever import BM25Retriever
from retrieval.seed.dense_retriever import DenseRetriever
from retrieval.seed.hybrid import retrieve_concurrent, rrf_merge
from tests.metrics import recall_at_k, precision_at_k, mrr as mrr_fn

CASES_PATH = os.getenv("CASES_PATH", "data/all_cases.json")
FULL_GT1   = os.getenv("FULL_GT1_PATH", "data/gt1_queries.json")   # used only to find train cases
KS    = [int(k) for k in os.getenv("EVAL_KS", "5,10").split(",")]
DEPTH = max(KS + [100])

# ── Corpus: same text construction as scripts/ingest_generic.py ──────────────
def build_text(sections):
    parts = []
    for key in ("caption", "header", "body", "conclusion"):
        val = sections.get(key) or {}
        val = val.get("text", "") if isinstance(val, dict) else val
        if val:
            parts.append(val.strip())
    return "\n\n".join(parts)

cases = json.load(open(CASES_PATH, encoding="utf-8"))["cases"]

# Dense corpus: full text, as indexed by scripts/ingest_generic.py
dense_corpus = [{"id": c["doc_id"], "text": build_text(c["sections"])}
                for c in cases if c.get("sections") and build_text(c["sections"])]

# BM25 corpus: body section only, exactly as api/retrieve.py builds it.
# CORPUS_SOURCE=api pulls it live from Component A (same call the API makes);
# default reads the same body text from the local all_cases.json snapshot.
if os.getenv("CORPUS_SOURCE", "local") == "api":
    from api.corpus_loader import fetch_corpus_from_api
    bm25_corpus = fetch_corpus_from_api()
else:
    bm25_corpus = [{"id": c["doc_id"], "text": c["sections"]["body"]["text"]}
                   for c in cases if (c.get("sections") or {}).get("body", {}).get("text")]

# ── Ground truth and subsets ─────────────────────────────────────────────────
gt1 = json.load(open(GT1_PATH, encoding="utf-8"))
train_cases = {i for g in json.load(open(FULL_GT1, encoding="utf-8"))
               if g.get("split") == "train" for i in g["relevant_ids"]}
subsets = {
    "all":         gt1,
    "eval":        [g for g in gt1 if g.get("split") in ("eval", "both")],
    "eval-unseen": [g for g in gt1 if g.get("split") in ("eval", "both")
                    and not set(g["relevant_ids"]) & train_cases],
}

# ── Retrievers ───────────────────────────────────────────────────────────────
def dense(mode, collection, ckpt=None):
    r = DenseRetriever(mode=mode, collection_name=collection, checkpoint_path=ckpt)
    if r.collection.count() != len(dense_corpus):   # index once; reuse on later runs
        r.index_corpus(dense_corpus)
    return r

bm25      = BM25Retriever(bm25_corpus)
dense_gen = dense("generic", COLLECTION_GENERIC)
dense_bge = dense("finetuned", COLLECTION_BGEM3_FINETUNED, BGE_FT_CKPT) if BGE_FT_CKPT else None
dense_ang = dense("finetuned", COLLECTION_ANGLEBERT_FINETUNED, ANGLEBERT_CKPT) if ANGLEBERT_CKPT else None

hybrid = lambda d: (lambda q: rrf_merge(*retrieve_concurrent(q, bm25, d, DEPTH), k=RRF_K))
ROWS = {"1  Sparse-only (BM25) [Luan et al.]":                lambda q: bm25.search(q, DEPTH),
        "2  Dense-only, generic BGE-M3":        lambda q: dense_gen.search(q, DEPTH)}
if dense_ang: ROWS["3a Dense-only, AnglE-BERT (FT) [Jayawardena et al.]"] = lambda q: dense_ang.search(q, DEPTH)
if dense_bge: ROWS["3b Dense-only, BGE-M3 (FT)"]     = lambda q: dense_bge.search(q, DEPTH)
ROWS["4  Hybrid, generic BGE-M3 + RRF [Arulanandam & De Silva]"] = hybrid(dense_gen)
if dense_ang: ROWS["5b Hybrid, AnglE-BERT (FT) + RRF [supplementary]"] = hybrid(dense_ang)   # justifies the dense-leg choice
if dense_bge: ROWS["5  Hybrid, BGE-M3 (FT) + RRF [PROPOSED]"] = hybrid(dense_bge)
# Row 6: Hybrid, BGE-M3 (FT) + adaptive RRF (QAFM)  -> PP2 / F1 scope

# ── Scoring ──────────────────────────────────────────────────────────────────
def score(fn, items):
    acc = {f"R@{k}": 0.0 for k in KS} | {f"P@{k}": 0.0 for k in KS} | {"MRR": 0.0}
    for it in items:
        rel = set(it["relevant_ids"])
        res = [i for i, _ in fn(it["query"])]
        for k in KS:
            acc[f"R@{k}"] += recall_at_k(res, rel, k)
            acc[f"P@{k}"] += precision_at_k(res, rel, k)
        acc["MRR"] += mrr_fn(res, rel)
    n = len(items) or 1
    return {m: round(v / n, 4) for m, v in acc.items()}

results = {"gt1_path": GT1_PATH, "n": {s: len(v) for s, v in subsets.items()},
           "rows": {name: {s: score(fn, items) for s, items in subsets.items()}
                    for name, fn in ROWS.items()}}
OUT_DIR = "evidence/ablation_study"
os.makedirs(OUT_DIR, exist_ok=True)
json.dump(results, open(f"{OUT_DIR}/ablation_results.json", "w", encoding="utf-8"), indent=2)

cols = [f"R@{k}" for k in KS] + [f"P@{k}" for k in KS] + ["MRR"]
for s in subsets:
    print(f"\n[{s}]  n={results['n'][s]}")
    print(f"{'':60}" + "".join(f"{c:>8}" for c in cols))
    for name in ROWS:
        print(f"{name:60}" + "".join(f"{results['rows'][name][s][c]:>8.4f}" for c in cols))

# ── Novelty deltas (Recall@K) ────────────────────────────────────────────────
R = results["rows"]
pairs = [("5  Hybrid, BGE-M3 (FT) + RRF [PROPOSED]", "1  Sparse-only (BM25) [Luan et al.]",                          "vs Luan et al. (sparse-only)"),
         ("5  Hybrid, BGE-M3 (FT) + RRF [PROPOSED]", "3a Dense-only, AnglE-BERT (FT) [Jayawardena et al.]",          "vs Jayawardena et al. (domain dense-only)"),
         ("5  Hybrid, BGE-M3 (FT) + RRF [PROPOSED]", "4  Hybrid, generic BGE-M3 + RRF [Arulanandam & De Silva]",     "vs Arulanandam & De Silva (generic hybrid)"),
         ("5  Hybrid, BGE-M3 (FT) + RRF [PROPOSED]", "3b Dense-only, BGE-M3 (FT)",                                   "sparse leg kept (same FT embeddings)"),
         ("5  Hybrid, BGE-M3 (FT) + RRF [PROPOSED]", "5b Hybrid, AnglE-BERT (FT) + RRF [supplementary]",             "dense leg: BGE-M3 vs AnglE-BERT")]
print("\nNovelty deltas (eval subset)")
for a, b, label in pairs:
    if a in R and b in R:
        print(f"  {label:44}" + "".join(f"  ΔR@{k}={R[a]['eval'][f'R@{k}'] - R[b]['eval'][f'R@{k}']:+.4f}" for k in KS)
              + f"  ΔMRR={R[a]['eval']['MRR'] - R[b]['eval']['MRR']:+.4f}")

# ── Evidence tables (CSV + PNG) ──────────────────────────────────────────────
import csv, datetime
stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
for s in subsets:
    with open(f"{OUT_DIR}/ablation_table_{s}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["Row"] + cols)
        for name in ROWS: w.writerow([name] + [results["rows"][name][s][c] for c in cols])

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    NAVY, PROP, BEST, GRID = "#1F3864", "#E2F0D9", "#1A5E20", "#BFBFBF"
    for s in subsets:
        names = list(ROWS)
        cells = [[n.split("  ", 1)[0].strip() if "  " in n else n.split(" ", 1)[0],
                  (n.split("  ", 1)[1] if "  " in n else n.split(" ", 1)[1])]
                 + [f"{results['rows'][n][s][c]:.2f}" for c in cols] for n in names]
        best = {c: max(results["rows"][n][s][c] for n in names) for c in cols}
        fig_h = 0.6 + 0.36 * len(names)
        fig, ax = plt.subplots(figsize=(13, fig_h)); ax.axis("off")
        t = ax.table(cellText=cells, colLabels=["Row", "Configuration"] + cols,
                     colWidths=[0.05, 0.50] + [0.09] * len(cols), loc="upper center", cellLoc="center")
        t.auto_set_font_size(False); t.set_fontsize(10); t.scale(1, 1.6)
        for (r, c), cell in t.get_celld().items():
            cell.set_edgecolor(GRID)
            if c == 1 and r > 0: cell.set_text_props(ha="left"); cell._loc = "left"
            if r == 0:
                cell.set_facecolor(NAVY); cell.set_text_props(color="white", weight="bold")
                continue
            name = names[r - 1]
            if "PROPOSED" in name: cell.set_facecolor(PROP)
            if c >= 2 and results["rows"][name][s][cols[c - 2]] == best[cols[c - 2]]:
                cell.set_text_props(weight="bold", color=BEST)
        ax.set_title(f"Seed Stage Ablation (proposal Table 1)  |  subset: {s}  |  n = {results['n'][s]} expert-validated queries",
                     fontsize=12, weight="bold", loc="left", pad=6)
        ax.text(0, -0.02, f"GT: {GT1_PATH}  |  run: {stamp}  |  bold green = best per column  |  green row = proposed",
                 fontsize=8, color="#555555", transform=ax.transAxes, va="top")
        fig.savefig(f"{OUT_DIR}/ablation_table_{s}.png", dpi=200, bbox_inches="tight")
        plt.close(fig)

    # deltas image (eval subset)
    drows = [(label, *[R[a]["eval"][f"R@{k}"] - R[b]["eval"][f"R@{k}"] for k in KS],
              R[a]["eval"]["MRR"] - R[b]["eval"]["MRR"]) for a, b, label in pairs if a in R and b in R]
    fig, ax = plt.subplots(figsize=(11, 0.6 + 0.36 * len(drows))); ax.axis("off")
    dcols = ["Proposed (Row 5) vs"] + [f"ΔR@{k}" for k in KS] + ["ΔMRR"]
    t = ax.table(cellText=[[d[0]] + [f"{v:+.2f}" for v in d[1:]] for d in drows], colLabels=dcols,
                 colWidths=[0.52] + [0.12] * (len(dcols) - 1), loc="upper center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(10); t.scale(1, 1.6)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor(GRID)
        if r == 0: cell.set_facecolor(NAVY); cell.set_text_props(color="white", weight="bold"); continue
        if c == 0: cell.set_text_props(ha="left"); cell._loc = "left"
        else:
            v = drows[r - 1][c]
            cell.set_text_props(color=BEST if v > 0 else ("#B00020" if v < 0 else "#333333"), weight="bold")
    ax.set_title(f"Novelty deltas  |  subset: eval  |  n = {results['n']['eval']}", fontsize=12, weight="bold", loc="left", pad=6)
    fig.savefig(f"{OUT_DIR}/ablation_deltas_eval.png", dpi=200, bbox_inches="tight"); plt.close(fig)
    print(f"\nSaved tables (.png + .csv), deltas and results JSON in {OUT_DIR}/")
except ImportError:
    print(f"\nmatplotlib not installed (pip3 install matplotlib) -> CSV tables saved in {OUT_DIR}/, PNGs skipped")

    #GT1_PATH=data/gt1_expert.json python3 tests/run_ablation.py