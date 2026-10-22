import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retrieval.seed.bm25_retriever import BM25Retriever
from retrieval.seed.dense_retriever import DenseRetriever
from retrieval.seed.hybrid import retrieve_concurrent

CORPUS = [
    {"id": "c1", "text": "employer liable defective equipment"},
    {"id": "c2", "text": "dismissal fair hearing procedure"},
    {"id": "c3", "text": "landlord tenant lease breach"},
]


def setup():
    bm25 = BM25Retriever(CORPUS)
    dense = DenseRetriever(
        mode="generic",
        collection_name="legal_bge_m3_generic",
        chroma_path="/tmp/test_chroma_concurrent",
    )
    dense.index_corpus(CORPUS)
    return bm25, dense

#Concurrent retrieval returns two separate lists (sparse,dense).
def test_returns_two_lists():
    bm25, dense = setup()
    b, d = retrieve_concurrent("employer negligence", bm25, dense, top_k=3)
    assert isinstance(b, list) and isinstance(d, list)

#Both lists are non-empty
def test_both_lists_have_results():
    bm25, dense = setup()
    b, d = retrieve_concurrent("lease agreement", bm25, dense, top_k=2)
    assert len(b) > 0 and len(d) > 0

#Neither list exceeds the requested top_k
def test_top_k_respected():
    bm25, dense = setup()
    b, d = retrieve_concurrent("contract", bm25, dense, top_k=2)
    assert len(b) <= 2 and len(d) <= 2