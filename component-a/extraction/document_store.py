import json, sqlite3, os
from datetime import datetime
from .entity_extractor import extract_entities

DB_PATH   = "corpus/cases.db"
CASES_DIR = "corpus/cases"
STUBS_DIR = "corpus/stubs"

def init_db():
    os.makedirs(CASES_DIR, exist_ok=True)
    os.makedirs(STUBS_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS cases (
            doc_id          TEXT PRIMARY KEY,
            case_num        TEXT,
            court           TEXT,
            date            TEXT,
            lang            TEXT DEFAULT 'en',
            in_corpus       INTEGER DEFAULT 1,
            text_available  INTEGER DEFAULT 1,
            ocr_required    INTEGER DEFAULT 0,
            validity_status TEXT DEFAULT 'good_law',
            path            TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_case_num ON cases(case_num);
        CREATE INDEX IF NOT EXISTS idx_court    ON cases(court);

        CREATE VIRTUAL TABLE IF NOT EXISTS cases_fts
        USING fts5(doc_id UNINDEXED, section UNINDEXED, text);
    """)
    con.commit()
    return con

def ingest_document(text, doc_id, case_num, court, date, source_sha):
    sections, entities = extract_entities(text)

    record = {
        "doc_id":         doc_id,
        "case_num":       case_num,
        "court":          court,
        "date":           date,
        "lang":           "en",
        "in_corpus":      True,
        "text_available": True,
        "ocr_required":   False,
        "validity_status":"good_law",
        "sections":       sections,
        "entities": {
            "judges":    [e for e in entities if e["label"] == "JUDGE"],
            "counsel":   [e for e in entities if e["label"] == "COUNSEL"],
            "acts":      [e for e in entities if e["label"] == "ACT"],
            "citations": [e for e in entities if e["label"] == "CITATION"],
        },
        "chain": [],
        "provenance": {
            "source_dataset": "nuuuwan/lk_supreme_court_judgements",
            "revision":       source_sha,
            "extracted_at":   datetime.now().isoformat()
        }
    }

    path = os.path.join(CASES_DIR, f"{doc_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT OR REPLACE INTO cases
        (doc_id, case_num, court, date, lang,
         in_corpus, text_available, ocr_required, path)
        VALUES (?, ?, ?, ?, 'en', 1, 1, 0, ?)
    """, (doc_id, case_num, court, date, path))

    for name, sec in sections.items():
        if sec.get("text"):
            con.execute("INSERT INTO cases_fts VALUES (?, ?, ?)",
                        (doc_id, name, sec["text"]))

    con.commit()
    con.close()
    return record