"""
Integration test: confirms all 3 ChromaDB collections are queryable,
query embeddings are generated correctly, and results are surfaced.

Requires:
    - chroma_db/ with all 3 collections at 190 docs each
    - models/bge_m3_finetuned/   (BGE-M3 fine-tuned checkpoint)
    - models/anglebert_finetuned/ (AnglE-BERT fine-tuned checkpoint)
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pytest
from retrieval.seed.dense_retriever import DenseRetriever
from config import (
    COLLECTION_GENERIC,
    COLLECTION_BGEM3_FINETUNED,
    COLLECTION_ANGLEBERT_FINETUNED,
    BGE_FT_CKPT,
    ANGLEBERT_CKPT,
)

CHROMA_PATH = "chroma_db"
QUERY       = "employer liable for defective equipment in the workplace"
TOP_K       = 5
CORPUS_SIZE = 190

#Fixtures — one retriever per collection, shared across tests in the module

@pytest.fixture(scope="module")
def retriever_generic():
    return DenseRetriever(
        mode="generic",
        collection_name=COLLECTION_GENERIC,
        chroma_path=CHROMA_PATH,
    )


@pytest.fixture(scope="module")
def retriever_bge_finetuned():
    ckpt = BGE_FT_CKPT or "models/bge_m3_finetuned"
    return DenseRetriever(
        mode="finetuned",
        checkpoint_path=ckpt,
        collection_name=COLLECTION_BGEM3_FINETUNED,
        chroma_path=CHROMA_PATH,
    )


@pytest.fixture(scope="module")
def retriever_anglebert():
    ckpt = ANGLEBERT_CKPT or "models/anglebert_finetuned"
    return DenseRetriever(
        mode="finetuned",
        checkpoint_path=ckpt,
        collection_name=COLLECTION_ANGLEBERT_FINETUNED,
        chroma_path=CHROMA_PATH,
    )

#Helper

def _query_embedding(retriever) -> np.ndarray:
    """Encode the shared query and return the raw embedding array."""
    return retriever.model.encode([QUERY], normalize_embeddings=True)



#Collection presence

class TestCollectionSize:
    def test_generic_has_190_docs(self, retriever_generic):
        assert retriever_generic.collection.count() == CORPUS_SIZE

    def test_bge_finetuned_has_190_docs(self, retriever_bge_finetuned):
        assert retriever_bge_finetuned.collection.count() == CORPUS_SIZE

    def test_anglebert_has_190_docs(self, retriever_anglebert):
        assert retriever_anglebert.collection.count() == CORPUS_SIZE


#Query embedding generation

class TestQueryEmbedding:
    def test_generic_embedding_dim(self, retriever_generic):
        emb = _query_embedding(retriever_generic)
        assert emb.shape == (1, 1024), f"Expected (1, 1024), got {emb.shape}"

    def test_generic_embedding_normalized(self, retriever_generic):
        emb = _query_embedding(retriever_generic)
        assert abs(np.linalg.norm(emb[0]) - 1.0) < 1e-5

    def test_bge_finetuned_embedding_dim(self, retriever_bge_finetuned):
        emb = _query_embedding(retriever_bge_finetuned)
        assert emb.shape == (1, 1024), f"Expected (1, 1024), got {emb.shape}"

    def test_bge_finetuned_embedding_normalized(self, retriever_bge_finetuned):
        emb = _query_embedding(retriever_bge_finetuned)
        assert abs(np.linalg.norm(emb[0]) - 1.0) < 1e-5

    def test_anglebert_embedding_dim(self, retriever_anglebert):
        emb = _query_embedding(retriever_anglebert)
        assert emb.shape == (1, 1024), f"Expected (1, 1024), got {emb.shape}"

    def test_anglebert_embedding_normalized(self, retriever_anglebert):
        emb = _query_embedding(retriever_anglebert)
        assert abs(np.linalg.norm(emb[0]) - 1.0) < 1e-5

    def test_finetuned_embeddings_differ_from_generic(
        self, retriever_generic, retriever_bge_finetuned
    ):
        """Fine-tuned model must produce a different query vector than base."""
        generic_emb   = _query_embedding(retriever_generic)[0]
        finetuned_emb = _query_embedding(retriever_bge_finetuned)[0]
        cosine_sim = float(np.dot(generic_emb, finetuned_emb))
        # They should not be identical (sim < 1.0); a small difference confirms fine-tuning
        assert cosine_sim < 1.0, "Fine-tuned and generic embeddings are identical — checkpoint not loaded"


#Result surfacing

class TestResultSurfacing:
    def test_generic_returns_top_k(self, retriever_generic):
        results = retriever_generic.search(QUERY, top_k=TOP_K)
        assert len(results) == TOP_K

    def test_bge_finetuned_returns_top_k(self, retriever_bge_finetuned):
        results = retriever_bge_finetuned.search(QUERY, top_k=TOP_K)
        assert len(results) == TOP_K

    def test_anglebert_returns_top_k(self, retriever_anglebert):
        results = retriever_anglebert.search(QUERY, top_k=TOP_K)
        assert len(results) == TOP_K

    def test_generic_scores_descending(self, retriever_generic):
        scores = [s for _, s in retriever_generic.search(QUERY, top_k=TOP_K)]
        assert scores == sorted(scores, reverse=True)

    def test_bge_finetuned_scores_descending(self, retriever_bge_finetuned):
        scores = [s for _, s in retriever_bge_finetuned.search(QUERY, top_k=TOP_K)]
        assert scores == sorted(scores, reverse=True)

    def test_anglebert_scores_descending(self, retriever_anglebert):
        scores = [s for _, s in retriever_anglebert.search(QUERY, top_k=TOP_K)]
        assert scores == sorted(scores, reverse=True)

    def test_generic_scores_in_valid_range(self, retriever_generic):
        for _, score in retriever_generic.search(QUERY, top_k=TOP_K):
            assert -1.0 <= score <= 1.0, f"Score {score} out of cosine range"

    def test_finetuned_rankings_differ_from_generic(
        self, retriever_generic, retriever_bge_finetuned
    ):
        """Fine-tuned collection must return a different ranking than generic."""
        generic_ids   = [i for i, _ in retriever_generic.search(QUERY, top_k=TOP_K)]
        finetuned_ids = [i for i, _ in retriever_bge_finetuned.search(QUERY, top_k=TOP_K)]
        assert generic_ids != finetuned_ids, "Generic and fine-tuned returned identical rankings"