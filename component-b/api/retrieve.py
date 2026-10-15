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


@app.post("/retrieve")
def retrieve(req: RetrieveRequest):
    b, d = retrieve_concurrent(req.query, bm25, dense, TOP_K)
    h = rrf_merge(b, d)
    return {
        "hybrid": [{"id": i, "score": s} for i, s in h],
    }


# uvicorn component_b.api.retrieve:app --port 8001 --reload