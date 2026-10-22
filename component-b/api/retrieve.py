import dataclasses
import json
import sys
import os
import httpx
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from pydantic import BaseModel

# TODO : add COLLECTION_BGE_M3_FINETUNED, CHECKPOINT_PATH to config imports
from config import TOP_K, CORPUS_PATH, COLLECTION_GENERIC, NEO4J_USE_MOCK
from retrieval.seed.bm25_retriever import BM25Retriever
from retrieval.seed.dense_retriever import DenseRetriever
from retrieval.seed.hybrid import retrieve_concurrent, rrf_merge
from retrieval.expand.traversal import expand
from api.corpus_loader import fetch_corpus_from_api
from api.response_enrichment import enrich_cluster

bm25: BM25Retriever = None
dense: DenseRetriever = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bm25, dense
    if NEO4J_USE_MOCK:
        corpus = json.load(open(CORPUS_PATH))
    else:
        corpus = fetch_corpus_from_api()
    bm25 = BM25Retriever(corpus)
    # TODO : replace with mode="finetuned", collection_name=COLLECTION_BGE_M3_FINETUNED, checkpoint_path=CHECKPOINT_PATH
    dense = DenseRetriever(
        mode="generic",
        collection_name=COLLECTION_GENERIC,
    )
    yield

app = FastAPI(title="Component B — Retrieval", version="0.1.0", lifespan=lifespan)

class RetrieveRequest(BaseModel):
    query: str
    top_k: int = TOP_K
    debug: bool = False

def _get_case_meta(case_id: str) -> dict:
    try:
        resp = httpx.get(
            f"https://component-a-api.onrender.com/cases/{case_id}",
            timeout=10.0
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}

@app.post("/retrieve")
def retrieve(req: RetrieveRequest):
    #Retrieval
    b, d = retrieve_concurrent(req.query, bm25, dense, req.top_k)
    h = rrf_merge(b, d)
    #Graph Expansion
    seed_ids = [item[0] for item in h[:req.top_k]]
    clusters = expand(seed_ids)
    for cluster, (_, score) in zip(clusters, h[:req.top_k]):
        cluster.rrf_score = score

    if req.debug:
        return {
            "bm25":    [{"id": i, "score": s} for i, s in b], #Debugging Only
            "dense":   [{"id": i, "score": s} for i, s in d], #Debugging Only
            "hybrid":  [{"id": i, "score": s} for i, s in h], #Debugging Only
            "clusters": [enrich_cluster(c, _get_case_meta(c.seed_id)) for c in clusters], #To be consumed by downstream RAG (C)
        }

    return {"clusters": [enrich_cluster(c, _get_case_meta(c.seed_id)) for c in clusters]}

#uvicorn api.retrieve:app --reload --port 8000