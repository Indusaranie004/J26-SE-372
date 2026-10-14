import os
from typing import List, Dict, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class DenseRetriever:
    """
    Dense semantic retriever backed by BGE-M3 (or a fine-tuned checkpoint) + ChromaDB.

    Modes
    -----
    "generic"   – BAAI/bge-m3 base weights → legal_bge_m3_generic          (rows 2 & 5)
    "finetuned" – checkpoint at checkpoint_path → named collection           (rows 3, 4, 6)
                  Row 3: ANGLEBERT_CKPT  → COLLECTION_ANGLEBERT_FINETUNED
                  Row 4: BGE_FT_CKPT     → COLLECTION_BGEM3_FINETUNED
    """

    def __init__(
        self,
        mode: str = "generic",
        checkpoint_path: str | None = None,
        collection_name: str | None = None,
        chroma_path: str = "./chroma_db",
    ):
        # Validate mode and required params
        if mode not in ("generic", "finetuned"):
            raise ValueError(f"mode must be \"generic\" or \"finetuned\", got \"{mode}\"")
        if mode == "finetuned" and not checkpoint_path:
            raise ValueError("checkpoint_path is required when mode=\"finetuned\"")
        if not collection_name:
            raise ValueError("collection_name is required")

        self.mode            = mode
        self.collection_name = collection_name

        # Load base BGE-M3 weights, or a fine-tuned checkpoint if provided
        model_source = checkpoint_path if mode == "finetuned" else "BAAI/bge-m3"
        self.model   = SentenceTransformer(model_source)

        # Connect to ChromaDB on disk (persistent across runs)
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create the target collection with cosine similarity space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Indexing ────────────────────────────────────────────────────────────────

    def index_corpus(self, corpus: List[Dict]) -> None:
        """
        Encode all documents and upsert into ChromaDB.
        corpus: [{"id": str, "text": str}, ...]
        Component B owns this in both mock and production modes.
        """
        if not corpus:
            return

        ids        = [d["id"]   for d in corpus]
        texts      = [d["text"] for d in corpus]

        # Encode all texts in one batched pass; normalize so cosine = dot product
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).tolist()

        # Upsert: insert new docs, update existing ones with same id
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
        )

    # ── Retrieval ───────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """
        Encode the query, find the top_k nearest neighbours in ChromaDB.
        Returns [(doc_id, similarity_score), ...] sorted descending.
        ChromaDB returns cosine distance d ∈ [0, 2]; similarity = 1 - d.
        """
        # Encode query as a single-item batch
        q_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        # Guard against requesting more results than the collection holds
        results = self.collection.query(
            query_embeddings=q_emb,
            n_results=min(top_k, self.collection.count() or 1),
            include=["distances"],
        )

        ids       = results["ids"][0]
        distances = results["distances"][0]

        # Convert distance → similarity and return as (id, score) pairs
        return [(doc_id, 1.0 - dist) for doc_id, dist in zip(ids, distances)]