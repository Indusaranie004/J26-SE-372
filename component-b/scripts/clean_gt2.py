"""
Clean GT2 against Component A's knowledge graph.

Input : data/gt2_raw.json      (text-drawn triplets — never modified)
Output: data/gt2_clean.json    (triplets whose node AND edge exist in the graph)
        data/gt2_removed.json  (dropped triplets + counts = A's coverage report)

Rule (isolates B's traversal from A's graph-build gaps):
    keep a triplet only if a DIRECT 1-hop edge from the seed to a matching node exists.
    - judicial_treatment     : (seed)-[:TREATED_BY]->(case)      match on case_name
    - legislative_foundation : (seed)-[:INVOLVES_ACT]->(act)     match on act name
    - litigation_history     : (seed)-[:APPEALED_FROM]->(case)   match on case_num

Names in gt2_raw are written as in the judgment text; A's stub IDs are slugs of
the cited text, so matching is fuzzy. A raw triplet may match several nodes
(e.g. "Manawadu v. AG" and "Manawadu v. The AG" stubs) — all are kept in
matched_ids, and the triplet counts as found if traversal returns any of them.

"""
import json
import re
import sys
from difflib import SequenceMatcher

sys.path.insert(0, ".")

RAW_PATH     = "data/gt2_raw.json"
CLEAN_PATH   = "data/gt2_clean.json"
REMOVED_PATH = "data/gt2_removed.json"

THRESHOLD = {                       # fuzzy match cut-offs (0–1)
    "judicial_treatment":     0.85,
    "legislative_foundation": 0.85,
    "litigation_history":     0.90,
}
CATEGORIES = list(THRESHOLD)


# ── Direct 1-hop lookups (independent of traversal.py) ──────────────────────
Q_TREATED = """
    MATCH (:Case {doc_id: $sid})-[:TREATED_BY]->(t:Case)
    RETURN DISTINCT t.doc_id AS id, coalesce(t.case_name, t.case_num, t.doc_id) AS label
"""
Q_ACTS = """
    MATCH (:Case {doc_id: $sid})-[:INVOLVES_ACT]->(a:Act)
    RETURN DISTINCT a.act_id AS id, coalesce(a.name, a.act_id) AS label
"""
Q_APPEALS = """
    MATCH (:Case {doc_id: $sid})-[:APPEALED_FROM]->(l:Case)
    RETURN DISTINCT l.doc_id AS id, coalesce(l.case_num, l.num, l.doc_id) AS label
"""
QUERIES = {
    "judicial_treatment":     Q_TREATED,
    "legislative_foundation": Q_ACTS,
    "litigation_history":     Q_APPEALS,
}


def fetch_neighbours(session, seed_id: str) -> dict:
    """{category: [{"id":..., "label":...}]} — every node directly linked to the seed."""
    return {cat: [dict(r) for r in session.run(q, sid=seed_id)]
            for cat, q in QUERIES.items()}


# ── Name normalisation ──────────────────────────────────────────────────────
_REPORT_RX = re.compile(r"[\[\(]?\d.*$")     # case names hold no digits: cut at first year/report ref


def norm_case_name(s: str) -> str:
    s = s.lower()
    s = re.sub(r"^stub-", "", s)
    s = _REPORT_RX.sub(" ", s)                       # drop law-report citations / years
    s = re.sub(r"\b(vs?\.?|versus)\b", " v ", s)
    s = re.sub(r"\bthe\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())


def norm_act(s: str) -> str:
    s = s.lower()
    s = re.sub(r"^act-|-unknown$|-\d{4}$", "", s)
    s = re.sub(r"\bno\.?\s*\d+\b|\bof\s+\d{4}\b|\(.*?\)", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(s.split())


def norm_case_num(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def raw_key(cat: str, item: dict) -> str:
    if cat == "judicial_treatment":
        return norm_case_name(item["cited_name"])
    if cat == "legislative_foundation":
        return norm_act(item["act_name"])
    return norm_case_num(item["case_num"])


def node_key(cat: str, node: dict) -> str:
    if cat == "judicial_treatment":
        return norm_case_name(node["label"])
    if cat == "legislative_foundation":
        return norm_act(node["label"])
    return norm_case_num(node["label"])


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b or a in b or b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


# ── Cleaning ────────────────────────────────────────────────────────────────
def clean_seed(entry: dict, neighbours: dict):
    kept, removed = {}, []
    for cat in CATEGORIES:
        kept[cat] = []
        for item in entry["expected"].get(cat, []):
            key = raw_key(cat, item)
            matches = [n["id"] for n in neighbours.get(cat, [])
                       if similarity(key, node_key(cat, n)) >= THRESHOLD[cat]]
            if matches:
                kept[cat].append({**item, "matched_ids": sorted(set(matches))})
            else:
                removed.append({"category": cat, **item, "reason": "no_direct_edge_to_matching_node"})
    return kept, removed


def run(raw: list, neighbour_fn):
    clean, removed_all = [], []
    totals = {c: {"raw": 0, "kept": 0} for c in CATEGORIES}

    for entry in raw:
        kept, removed = clean_seed(entry, neighbour_fn(entry["seed_id"]))
        for c in CATEGORIES:
            totals[c]["raw"]  += len(entry["expected"].get(c, []))
            totals[c]["kept"] += len(kept[c])
        clean.append({k: v for k, v in entry.items() if k != "expected"} | {"expected": kept})
        if removed:
            removed_all.append({"seed_id": entry["seed_id"], "removed": removed})

    for c in CATEGORIES:
        t = totals[c]
        t["removed"] = t["raw"] - t["kept"]
        t["coverage"] = round(t["kept"] / t["raw"], 3) if t["raw"] else None
    report = {"summary": totals, "by_seed": removed_all}
    return clean, report


def main():
    import config  # noqa: F401 — loads .env before neo4j_client reads NEO4J_* vars
    from retrieval.expand.neo4j_client import _get_driver

    raw = json.load(open(RAW_PATH, encoding="utf-8"))
    with _get_driver().session() as session:
        clean, report = run(raw, lambda sid: fetch_neighbours(session, sid))

    json.dump(clean,  open(CLEAN_PATH,   "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(report, open(REMOVED_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"{'category':<24}{'raw':>6}{'kept':>6}{'removed':>9}{'coverage':>10}")
    for c, t in report["summary"].items():
        print(f"{c:<24}{t['raw']:>6}{t['kept']:>6}{t['removed']:>9}{str(t['coverage']):>10}")
    print(f"\nWrote {CLEAN_PATH} and {REMOVED_PATH}")


if __name__ == "__main__":
    main()
