import httpx

COMPONENT_A_BASE = "https://component-a-api.onrender.com"


def fetch_corpus_from_api() -> list:
    # Fetch all doc_ids from /manifest
    manifest = httpx.get(f"{COMPONENT_A_BASE}/manifest", timeout=60.0).json()
    doc_ids = manifest["doc_ids"]

    corpus = []
    for did in doc_ids:
        resp = httpx.get(f"{COMPONENT_A_BASE}/cases/{did}/sections/body", timeout=30.0)
        if resp.status_code == 200 and "text" in resp.json():
            corpus.append({"id": did, "text": resp.json()["text"]})
    return corpus