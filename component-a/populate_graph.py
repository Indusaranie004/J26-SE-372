"""
Run from component-a/ directory:
    python populate_graph.py
"""
import os, json, glob, re
from extraction.treatment_extractor import extract_treatments
from extraction.neo4j_writer import (
    init_constraints, write_case_node, write_judge_edge,
    write_act_edge, write_treatment_edge, write_chain_edges
)

def main():
    init_constraints()

    cases_dir = "corpus/cases"
    json_files = glob.glob(f"{cases_dir}/*.json")
    print(f"Found {len(json_files)} case records\n")

    total_treatment_edges = 0
    total_judge_edges = 0
    total_act_edges = 0
    total_chain_edges = 0

    for path in json_files:
        rec = json.load(open(path, encoding="utf-8"))
        doc_id   = rec["doc_id"]
        case_num = rec.get("case_num", doc_id)
        court    = rec.get("court", "SC")
        date     = rec.get("date", "unknown")

        # Write Case node
        write_case_node(doc_id, case_num, court, date)

        # Write Judge edges
        for judge in rec["entities"].get("judges", []):
            write_judge_edge(doc_id, judge["text"])
            total_judge_edges += 1

        # Write Act edges
        for act in rec["entities"].get("acts", []):
            write_act_edge(
                doc_id,
                act["text"],
                act.get("act_year"),
                act.get("section"),
                act.get("act_number")
            )
            total_act_edges += 1

        # Write litigation chain edges
        chain = rec.get("chain", [])
        if chain:
            write_chain_edges(doc_id, chain)
            total_chain_edges += len(
                [e for e in chain if e.get("court") != "SC"]
            )

        # Extract and write treatment edges
        body_text = rec["sections"].get("body", {}).get("text", "")
        body_start = rec["sections"].get("body", {}).get("char_start", 0)

        # Adjust citation offsets to be relative to body_text
        citations = []
        for c in rec["entities"].get("citations", []):
            citations.append({
                "text": c["text"],
                "start": c["start"],
                "body_offset": max(0, c["start"] - body_start)
            })

        treatments = extract_treatments(body_text, doc_id, citations)

        for t in treatments:
            write_treatment_edge(
                doc_id,
                t["treated_case_name"],
                t["treatment_type"],
                date,
                t["evidence"],
                t["char_offset"]
            )
            total_treatment_edges += 1

        print(f"  ✓ {doc_id[:50]:<50} | "
              f"judges: {len(rec['entities'].get('judges',[]))} | "
              f"acts: {len(rec['entities'].get('acts',[]))} | "
              f"treatment edges: {len(treatments)}")

    print(f"\n{'='*60}")
    print(f"Done.")
    print(f"  Judge edges:     {total_judge_edges}")
    print(f"  Act edges:       {total_act_edges}")
    print(f"  Chain edges:     {total_chain_edges}")
    print(f"  Treatment edges: {total_treatment_edges}")
    print(f"\nCheck Neo4j Browser:")
    print(f"  MATCH (a:Case)-[t:TREATED_BY]->(b:Case) RETURN a,t,b LIMIT 20")

if __name__ == "__main__":
    main()