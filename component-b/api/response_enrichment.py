import dataclasses
from retrieval.expand.models import PrecedentCluster

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
    if not ctx["legislation"]:
        legislation_parsed = case_meta.get("legislation_parsed")

        if legislation_parsed is True:
            ctx["legislation"] = "Constitutional articles cited — statutory Acts not captured for this case."
        else:
            ctx["legislation"] = "No legislation data available."

    return d
