import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from retrieval.seed.bm25_retriever import BM25Retriever

CORPUS = [
    {'id': 'c1', 'text': 'employer liable defective equipment workplace'},
    {'id': 'c2', 'text': 'dismissal procedure fair hearing employee'},
    {'id': 'c3', 'text': 'landlord tenant lease agreement breach'},
    {'id': 'c4', 'text': 'negligence duty of care personal injury'},
    {'id': 'c5', 'text': 'contract formation offer acceptance consideration'},
]

#Confirms that the retriever returns results for a query within the specified k
def test_returns_results():
    r = BM25Retriever(CORPUS)
    results = r.search('employer liable', top_k=3)
    assert len(results) == 3

#Confirms that the top result is the most relevant document(highest term overlap) for a given query
def test_top_result_correct():
    r = BM25Retriever(CORPUS)
    results = r.search('employer liable defective equipment', top_k=5)
    ids = [doc_id for doc_id, _ in results]
    assert ids[0] == 'c1'

#Confirms scores are in relevance descending order for a given query
def test_scores_descending():
    r = BM25Retriever(CORPUS)
    results = r.search('negligence duty care', top_k=5)
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)

#Checks if the retriever respects the top_k parameter and returns no more than k results
def test_top_k_respected():
    r = BM25Retriever(CORPUS)
    results = r.search('contract', top_k=2)
    assert len(results) <= 2