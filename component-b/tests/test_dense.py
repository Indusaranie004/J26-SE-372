import sys
import os
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from retrieval.seed.dense_retriever import DenseRetriever


CHROMA_TEST_DIR = "/tmp/test_chroma_dense"

CORPUS = [
    {"id": "c1", "text": "employer liable for defective equipment in the workplace"},
    {"id": "c2", "text": "dismissal must follow fair procedure and hearing"},
    {"id": "c3", "text": "landlord and tenant lease agreement breach of contract"},
    {"id": "c4", "text": "negligence duty of care personal injury damages"},
    {"id": "c5", "text": "offer acceptance consideration contract formation"},
]


@pytest.fixture(scope="module")
def retriever():
    """Single retriever shared across all tests; cleaned up after module."""
    r = DenseRetriever(
        mode="generic",
        collection_name="legal_bge_m3_generic",
        chroma_path=CHROMA_TEST_DIR,
    )
    r.index_corpus(CORPUS)
    yield r
    shutil.rmtree(CHROMA_TEST_DIR, ignore_errors=True)

#Search returns exactly top_k results.
def test_returns_results(retriever):
    results = retriever.search("employer liable", top_k=3)
    assert len(results) == 3

#BGE-M3 ranks a semantically related doc first, not just keyword match
def test_top_result_semantically_relevant(retriever):
    results = retriever.search("workplace injury employer responsibility", top_k=5)
    top_id  = results[0][0]
    # c1 (employer/workplace) or c4 (injury/duty of care) are both acceptable
    assert top_id in ("c1", "c4")

#Results are returned in descending order of relevance for a given query
def test_scores_descending(retriever):
    results = retriever.search("contract law", top_k=5)
    scores  = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)

#Tests more than top_k results are never returned
def test_top_k_respected(retriever):
    results = retriever.search("negligence", top_k=2)
    assert len(results) <= 2

#Test that the collection name is stored correctly on the object
def test_generic_collection_name(retriever):
    assert retriever.collection_name == "legal_bge_m3_generic"

#mode="finetuned" without a checkpoint must fail loudly, not silently fall back to base BGE-M3.
def test_finetuned_mode_requires_checkpoint():
    with pytest.raises(ValueError, match="checkpoint_path"):
        DenseRetriever(
            mode="finetuned",
            collection_name="legal_bge_m3_finetuned",
            chroma_path=CHROMA_TEST_DIR,
        )