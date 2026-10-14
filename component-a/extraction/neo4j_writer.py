import os, json
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
    return _driver

def init_constraints():
    """Create uniqueness constraints — run once at startup."""
    with get_driver().session() as s:
        s.run("CREATE CONSTRAINT case_doc_id IF NOT EXISTS FOR (c:Case) REQUIRE c.doc_id IS UNIQUE")
        s.run("CREATE CONSTRAINT judge_name IF NOT EXISTS FOR (j:Judge) REQUIRE j.name IS UNIQUE")
        s.run("CREATE CONSTRAINT act_id IF NOT EXISTS FOR (a:Act) REQUIRE a.act_id IS UNIQUE")
    print("Constraints initialised.")

def write_case_node(doc_id, case_num, court, date, in_corpus=True,
                   validity_status="good_law"):
    with get_driver().session() as s:
        s.run("""
            MERGE (c:Case {doc_id: $doc_id})
            SET c.case_num        = $case_num,
                c.court           = $court,
                c.date            = $date,
                c.in_corpus       = $in_corpus,
                c.validity_status = $validity_status,
                c.valid_from      = $date
        """, doc_id=doc_id, case_num=case_num, court=court,
             date=date, in_corpus=in_corpus,
             validity_status=validity_status)

def write_stub_node(cited_name, stub_doc_id, court="SC"):
    """Create a stub node for a cited case not in the corpus."""
    with get_driver().session() as s:
        s.run("""
            MERGE (c:Case {doc_id: $doc_id})
            SET c.case_name      = $case_name,
                c.in_corpus      = false,
                c.text_available = false,
                c.court          = $court,
                c.validity_status = 'good_law'
        """, doc_id=stub_doc_id, case_name=cited_name, court=court)

def write_stub_json(stub_doc_id, cited_name, court="SC"):
    """Write stub JSON to corpus/stubs/ so API can serve it."""
    os.makedirs("corpus/stubs", exist_ok=True)
    path = f"corpus/stubs/{stub_doc_id}.json"
    if not os.path.exists(path):
        stub = {
            "doc_id":        stub_doc_id,
            "case_name":     cited_name,
            "court":         court,
            "in_corpus":     False,
            "text_available":False,
            "valid_from":    None,
            "valid_until":   None,
            "validity_status":"good_law",
            "invalidated_by": None
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stub, f, indent=2)

def make_stub_id(case_name):
    """Generate a consistent stub doc_id from a case name."""
    clean = case_name.lower()
    clean = clean.replace(" v. ", "-v-").replace(" v ", "-v-")
    clean = "".join(c if c.isalnum() or c == "-" else "-" for c in clean)
    clean = "-".join(p for p in clean.split("-") if p)
    return f"stub-{clean[:50]}"

def write_judge_edge(case_doc_id, judge_name):
    with get_driver().session() as s:
        s.run("""
            MERGE (c:Case {doc_id: $doc_id})
            MERGE (j:Judge {name: $name})
            MERGE (c)-[:DECIDED_BY]->(j)
        """, doc_id=case_doc_id, name=judge_name)

def write_act_edge(case_doc_id, act_name, act_year, section, act_number=None):
    act_id = f"act-{act_name[:30].lower().replace(' ','-')}-{act_year or 'unknown'}"
    with get_driver().session() as s:
        s.run("""
            MERGE (c:Case {doc_id: $doc_id})
            MERGE (a:Act  {act_id: $act_id})
            SET a.name       = $name,
                a.year       = $year,
                a.act_number = $act_number
            MERGE (c)-[r:INVOLVES_ACT]->(a)
            SET r.section = $section
        """, doc_id=case_doc_id, act_id=act_id,
             name=act_name, year=act_year,
             act_number=act_number, section=section)

def write_treatment_edge(treating_doc_id, treated_case_name,
                         treatment_type, effective_date,
                         evidence, char_offset):
    """Write TREATED_BY edge. Creates stub node if treated case not in corpus."""
    stub_id = make_stub_id(treated_case_name)

    # Ensure both nodes exist
    write_stub_node(treated_case_name, stub_id)
    write_stub_json(stub_id, treated_case_name)

    with get_driver().session() as s:
        s.run("""
            MERGE (treating:Case {doc_id: $treating_id})
            MERGE (treated:Case  {doc_id: $treated_id})
            CREATE (treating)-[:TREATED_BY {
                treatment_type:  $treatment_type,
                effective_date:  $effective_date,
                evidence:        $evidence,
                char_offset:     $char_offset,
                ingested_at:     $now
            }]->(treated)
        """, treating_id=treating_doc_id,
             treated_id=stub_id,
             treatment_type=treatment_type,
             effective_date=effective_date,
             evidence=evidence,
             char_offset=char_offset,
             now=datetime.now().isoformat())

    # Update validity if overruled
    if treatment_type == "overruled":
        with get_driver().session() as s:
            s.run("""
                MATCH (c:Case {doc_id: $doc_id})
                SET c.validity_status = 'no_longer_good_law',
                    c.valid_until     = $date,
                    c.invalidated_by  = $by
            """, doc_id=stub_id,
                 date=effective_date,
                 by=treating_doc_id)

def write_chain_edges(case_doc_id, chain):
    """Write APPEALED_FROM edges from litigation chain."""
    courts = [entry for entry in chain
              if entry.get("court") != "SC"]
    for entry in courts:
        lower_id = f"stub-{entry['court'].lower()}-{entry['num'].replace('/','-')[:20]}"
        with get_driver().session() as s:
            s.run("""
                MERGE (sc:Case    {doc_id: $sc_id})
                MERGE (lower:Case {doc_id: $lower_id})
                SET lower.case_num  = $num,
                    lower.court     = $court,
                    lower.place     = $place,
                    lower.in_corpus = false
                MERGE (sc)-[:APPEALED_FROM]->(lower)
            """, sc_id=case_doc_id,
                 lower_id=lower_id,
                 num=entry.get("num",""),
                 court=entry.get("court",""),
                 place=entry.get("place"))