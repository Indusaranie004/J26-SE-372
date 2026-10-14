import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import CORPUS_PATH, GT1_PATH, TOP_K, COLLECTION_GENERIC
from retrieval.seed.bm25_retriever import BM25Retriever
from retrieval.seed.dense_retriever import DenseRetriever
from retrieval.seed.hybrid import retrieve_concurrent, rrf_merge
from tests.metrics import recall_at_k, precision_at_k, mrr as mrr_fn

corpus = json.load(open(CORPUS_PATH))
gt1 = json.load(open(GT1_PATH))  # [{"query": str, "relevant_ids": [str]}]

bm25 = BM25Retriever(corpus)
dense = DenseRetriever(
    mode="generic",
    collection_name=COLLECTION_GENERIC,
)
dense.index_corpus(corpus)


def evaluate(name, get_results):
    r, p, m = [], [], []
    for item in gt1:
        rel = set(item["relevant_ids"])
        res = [i for i, _ in get_results(item["query"])]
        r.append(recall_at_k(res, rel, TOP_K))
        p.append(precision_at_k(res, rel, TOP_K))
        m.append(mrr_fn(res, rel))
    n = len(gt1)
    print(f"{name:<40} R@{TOP_K}={sum(r)/n:.4f} P@{TOP_K}={sum(p)/n:.4f} MRR={sum(m)/n:.4f}")


evaluate(
    "Row 1 — BM25 only",
    lambda q: bm25.search(q, TOP_K),
)
evaluate(
    "Row 2 — Dense only (generic BGE-M3)",
    lambda q: dense.search(q, TOP_K),
)
evaluate(
    "Row 5 — Hybrid static RRF (generic BGE-M3)",
    lambda q: rrf_merge(*retrieve_concurrent(q, bm25, dense, TOP_K)),
)
# Rows 3, 4, 6 — add here once checkpoints are available
# Row 7 — PP2,F1 scope (QAFM adaptive weights)