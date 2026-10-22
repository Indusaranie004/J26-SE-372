from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple

class BM25Retriever:

    def __init__(self, corpus: List[Dict]):
        """corpus: [{'id': str, 'text': str}, ...]"""
        self.ids = [d['id'] for d in corpus]
        tokenized = [d['text'].lower().split() for d in corpus]
        self.index = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        scores = self.index.get_scores(query.lower().split())
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(self.ids[i], float(s)) for i, s in ranked[:top_k]]