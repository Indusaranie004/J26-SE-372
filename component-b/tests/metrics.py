# R@K = hits_in_top_K / total_relevant of all relevant docs, how many did we find in top K?
def recall_at_k(retrieved: list, relevant: set, k: int) -> float:
    hits = sum(1 for d in retrieved[:k] if d in relevant)
    return hits / len(relevant) if relevant else 0.0

# P@K = hits_in_top_K / K — of the top K returned, how many are actually relevant?
def precision_at_k(retrieved: list, relevant: set, k: int) -> float:
    hits = sum(1 for d in retrieved[:k] if d in relevant)
    return hits / k if k else 0.0

# MRR = 1 / rank_of_first_hit — how high up was the first relevant result? (rank 1→1.0, rank 2→0.5, …)
def mrr(retrieved: list, relevant: set) -> float:
    for rank, doc_id in enumerate(retrieved, 1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0