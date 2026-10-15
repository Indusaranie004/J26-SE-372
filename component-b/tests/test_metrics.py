import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.metrics import recall_at_k, precision_at_k, mrr

RETRIEVED = ["c1", "c2", "c3", "c4", "c5"]
RELEVANT = {"c1", "c3"}

#c1 and c3 both in top 5, all relevant found → R@5 = 2/2 = 1.0
def test_recall_at_k_full():
    assert recall_at_k(RETRIEVED, RELEVANT, k=5) == 1.0

#Only c1 in top 1, c3 missed → R@1 = 1/2 = 0.5
def test_recall_at_k_partial():
    assert recall_at_k(RETRIEVED, RELEVANT, k=1) == 0.5

#c1 and c3 both in top 5 → 2/5 = 0.4
def test_precision_at_k():
    assert abs(precision_at_k(RETRIEVED, RELEVANT, k=5) - 0.4) < 1e-6 #Checks the result is within 0.000001 of 0.4. (Avoids floating-point precision issues (e.g. 0.3999999999 failing an exact equality check)).

#c1 is rank 1 → first hit immediately → MRR = 1/1 = 1.0
def test_mrr_first_hit():
    assert mrr(RETRIEVED, RELEVANT) == 1.0  # c1 is rank 1

#No relevant doc in list → MRR = 0.0
def test_mrr_no_hit():
    assert mrr(RETRIEVED, {"cx"}) == 0.0

#No relevant docs exist → R@5 = 0.0
def test_recall_empty_relevant():
    assert recall_at_k(RETRIEVED, set(), k=5) == 0.0