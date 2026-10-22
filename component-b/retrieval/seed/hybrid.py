from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from .bm25_retriever import BM25Retriever
from .dense_retriever import DenseRetriever


def retrieve_concurrent(
    query: str,
    bm25: BM25Retriever,
    dense: DenseRetriever,
    top_k: int,
) -> Tuple[List, List]:
    """Returns (bm25_results, dense_results) — two separate ranked lists."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_b = pool.submit(bm25.search, query, top_k)
        f_d = pool.submit(dense.search, query, top_k)
    return f_b.result(), f_d.result()

def rrf_merge(
    bm25_list: list,
    dense_list: list,
    k: int = 60,
    w_bm25: float = 0.5,
    w_dense: float = 0.5,
) -> list:
    """
    Reciprocal Rank Fusion.
    score(d) = w_bm25 / (k + rank_bm25(d)) + w_dense / (k + rank_dense(d))

    Default = static equal-weight fusion (rows 5 & 6).
    In PP2, F1 passes per-intent weights here for row 7 (QAFM).
    """
    bm25_rank = {i: r + 1 for r, (i, _) in enumerate(bm25_list)}
    dense_rank = {i: r + 1 for r, (i, _) in enumerate(dense_list)}

    all_ids = set(bm25_rank) | set(dense_rank)
    scores = {}
    for doc_id in all_ids:
        s = 0.0
        if doc_id in bm25_rank:
            s += w_bm25 / (k + bm25_rank[doc_id])
        if doc_id in dense_rank:
            s += w_dense / (k + dense_rank[doc_id])
        scores[doc_id] = s

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)