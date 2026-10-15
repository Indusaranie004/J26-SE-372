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

#Inject mock retrievers before tests run
api_module.bm25 = BM25Retriever(CORPUS)
api_module.dense = DenseRetriever(
    mode="generic",
    collection_name="legal_bge_m3_generic",
    chroma_path="/tmp/test_chroma_api",
)
api_module.dense.index_corpus(CORPUS)

client = TestClient(app)

#F1

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

#F2 

# Response body contains the "clusters" key.
def test_retrieve_response_has_clusters():
    res = client.post("/retrieve", json={"query": "employer negligence"})
    assert "clusters" in res.json()

#Clusters list is non-empty for a matching query.
def test_clusters_nonempty():
    res = client.post("/retrieve", json={"query": "dismissal"})
    assert len(res.json()["clusters"]) > 0

#Each cluster has seed_id, rrf_score, and legal_context.
def test_cluster_top_level_shape():
    res = client.post("/retrieve", json={"query": "lease"})
    for cluster in res.json()["clusters"]:
        assert "seed_id" in cluster
        assert "rrf_score" in cluster
        assert "legal_context" in cluster

#Legal_context contains the three required fields.
def test_cluster_legal_context_shape():
    res = client.post("/retrieve", json={"query": "employer negligence"})
    for cluster in res.json()["clusters"]:
        lc = cluster["legal_context"]
        assert "judicial_treatment" in lc
        assert "legislative_foundation" in lc
        assert "litigation_history" in lc

#Judicial_treatment, legislative_foundation, litigation_history are lists.
def test_cluster_legal_context_types():
    res = client.post("/retrieve", json={"query": "lease"})
    for cluster in res.json()["clusters"]:
        lc = cluster["legal_context"]
        assert isinstance(lc["judicial_treatment"], list)
        assert isinstance(lc["legislative_foundation"], list)
        assert isinstance(lc["litigation_history"], list)

#rrf_score is a positive float.
def test_cluster_rrf_score_positive():
    res = client.post("/retrieve", json={"query": "dismissal"})
    for cluster in res.json()["clusters"]:
        assert isinstance(cluster["rrf_score"], float)
        assert cluster["rrf_score"] > 0.0

#Cluster count does not exceed top_k.
def test_cluster_count_within_top_k():
    top_k = 2
    res = client.post("/retrieve", json={"query": "employer negligence", "top_k": top_k})
    assert len(res.json()["clusters"]) <= top_k

#Seed_id in each cluster matches an id returned in hybrid results.
def test_cluster_seed_ids_match_hybrid():
    res = client.post("/retrieve", json={"query": "lease"})
    body = res.json()
    hybrid_ids = {item["id"] for item in body["hybrid"]}
    for cluster in body["clusters"]:
        assert cluster["seed_id"] in hybrid_ids