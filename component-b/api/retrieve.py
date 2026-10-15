import dataclasses
import json
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from pydantic import BaseModel

# TODO : add COLLECTION_BGE_M3_FINETUNED, CHECKPOINT_PATH to config imports
from config import TOP_K, CORPUS_PATH, COLLECTION_GENERIC
from retrieval.seed.bm25_retriever import BM25Retriever
from retrieval.seed.dense_retriever import DenseRetriever
from retrieval.seed.hybrid import retrieve_concurrent, rrf_merge
from retrieval.expand.traversal import expand

bm25: BM25Retriever = None
dense: DenseRetriever = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bm25, dense
    corpus = json.load(open(CORPUS_PATH))
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
    return {
        "bm25":    [{"id": i, "score": s} for i, s in b], #Debugging Only
        "dense":   [{"id": i, "score": s} for i, s in d], #Debugging Only
        "hybrid":  [{"id": i, "score": s} for i, s in h], #Debugging Only
        "clusters": [dataclasses.asdict(c) for c in clusters], #To be consumed by downstream RAG (C)
    }

# uvicorn component_b.api.retrieve:app --port 8001 --reload