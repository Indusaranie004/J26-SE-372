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