import dataclasses
import re
from retrieval.expand.models import PrecedentCluster

def extract_legal_issue(body: str, max_chars: int = 800) -> str:
    paragraphs = [p.strip() for p in re.split(r'\n+', body) if p.strip()]
    skip_patterns = re.compile(
        r'^(decided on|before:|counsel:|appearance|for the petitioner|for the respondent|'
        r'in the supreme court|democratic socialist|republic of sri lanka|in the matter|'
        r'and (now )?between|and between|\d+$|sc\s*(appeal|fr|hc)|page \d)',
        re.IGNORECASE
    )
    for para in paragraphs:
        if not skip_patterns.match(para) and len(para) > 100:
            return para[:max_chars] + "…" if len(para) > max_chars else para
    return body[:max_chars] + "…"

def enrich_cluster(cluster: PrecedentCluster, case_meta: dict) -> dict:
    d = dataclasses.asdict(cluster)
    ctx = d["legal_context"]

    # --- judicial_treatment enrichment ---
    if not ctx["judicial_treatment"]:
        treatment_note = case_meta.get("treatment_note")
        is_stub = case_meta.get("is_stub")

        if treatment_note:
            ctx["judicial_treatment"] = treatment_note
        elif is_stub is True:
            ctx["judicial_treatment"] = "No treatment data: case cited but not in corpus (stub node)."
        elif is_stub is False:
            ctx["judicial_treatment"] = "No classifiable judicial treatment found in graph for this case."
        else:
            ctx["judicial_treatment"] = "Judicial treatment not yet assessed for this case."

    # --- litigation_history enrichment ---
    if not ctx["litigation_history"]:
        appeal_chain_parsed = case_meta.get("appeal_chain_parsed")

        if appeal_chain_parsed is True:
            ctx["litigation_history"] = "Appeal chain parsed but no DC/CA references found in caption."
        elif appeal_chain_parsed is False:
            ctx["litigation_history"] = "No appeal chain: case originated at Supreme Court."
        else:
            ctx["litigation_history"] = "Appeal chain not yet parsed for this case."

    # --- legislation enrichment ---
    if not ctx["legislative_foundation"]:
        legislation_parsed = case_meta.get("legislation_parsed")

        if legislation_parsed is True:
            ctx["legislative_foundation"] = "Constitutional articles cited — statutory Acts not captured for this case."
        else:
            ctx["legislative_foundation"] = "No legislative foundation data available."

    # --- summary ---
    sections = case_meta.get("sections", {})
    caption = (sections.get("caption", {}).get("text") or "").strip()
    body = (sections.get("body", {}).get("text") or "").strip()
    if body or caption:
        snippet = extract_legal_issue(body) if body else ""
        d["summary"] = f"{caption}\n\n{snippet}".strip() if caption else snippet
    else:
        d["summary"] = None

    return d