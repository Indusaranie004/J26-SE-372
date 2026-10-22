import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retrieval.seed.hybrid import rrf_merge

BM25_LIST = [("c1", 0.9), ("c2", 0.7), ("c3", 0.5)]
DENSE_LIST = [("c2", 0.95), ("c1", 0.6), ("c4", 0.4)]

#Results are in the descending order of their RRF scores.
def test_output_sorted():
    result = rrf_merge(BM25_LIST, DENSE_LIST)
    scores = [s for _, s in result]
    assert scores == sorted(scores, reverse=True)


#All document IDs from both lists are included in the merged result.
def test_union_of_ids():
    result = rrf_merge(BM25_LIST, DENSE_LIST)
    ids = {i for i, _ in result}
    assert ids == {"c1", "c2", "c3", "c4"}

#Docs in both lists score higher than docs in only one.
def test_overlap_doc_scores_higher():
    # c1 and c2 appear in both lists; c3/c4 appear in only one
    result = rrf_merge(BM25_LIST, DENSE_LIST)
    score_map = dict(result)
    overlap_min = min(score_map["c1"], score_map["c2"])
    single_max = max(score_map["c3"], score_map["c4"])
    assert overlap_min > single_max

#Validates that weights shift rankings as the foundation for adaptive weighting in QAFM. (PP2)
def test_custom_weights_shift_ranking():
    # High BM25 weight should push c1 (top BM25) above c2 (top dense)
    result = rrf_merge(BM25_LIST, DENSE_LIST, w_bm25=0.9, w_dense=0.1)
    ids = [i for i, _ in result]
    assert ids[0] == "c1"