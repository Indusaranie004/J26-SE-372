import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from api.retrieve import app
import api.retrieve as api_module

from retrieval.seed.bm25_retriever import BM25Retriever
from retrieval.seed.dense_retriever import DenseRetriever

CORPUS = [
    {"id": "c1", "text": "employer liable defective equipment"},
    {"id": "c2", "text": "dismissal fair hearing procedure"},
    {"id": "c3", "text": "landlord tenant lease breach"},
]

# Inject mock retrievers before tests run
api_module.bm25 = BM25Retriever(CORPUS)
api_module.dense = DenseRetriever(
    mode="generic",
    collection_name="legal_bge_m3_generic",
    chroma_path="/tmp/test_chroma_api",
)
api_module.dense.index_corpus(CORPUS)

client = TestClient(app)

#POST /retrieve returns HTTP 200 for a valid query.
def test_retrieve_status():
    res = client.post("/retrieve", json={"query": "employer negligence"})
    assert res.status_code == 200

#Response body contains the "hybrid" key.
def test_retrieve_response_keys():
    res = client.post("/retrieve", json={"query": "lease"})
    body = res.json()
    assert "hybrid" in body

#Hybrid list is non-empty for a matching query.
def test_retrieve_results_nonempty():
    res = client.post("/retrieve", json={"query": "dismissal"})
    body = res.json()
    assert len(body["hybrid"]) > 0

#Each hybrid result has "id" and "score" fields.
def test_retrieve_result_shape():
    res = client.post("/retrieve", json={"query": "contract"})
    for item in res.json()["hybrid"]:
        assert "id" in item and "score" in item