"""
Run from component-a/ directory:
    python ingest.py --corpus ../lk_supreme_court_judgements/data --limit 30
"""
import os, json, re, argparse, glob
from extraction.document_store import init_db, ingest_document

def find_rich_docs(base, limit=30):
    """Pick treatment-rich documents — ones containing citation treatment language."""
    keywords = [
        "distinguished", "overruled", "followed",
        "per incuriam", "not followed", "no longer good law",
        "wrongly decided", "decline to follow"
    ]
    rich = []
    # Walk all doc.txt files
    for txt_path in glob.glob(f"{base}/**/*.txt", recursive=True):
        try:
            text = open(txt_path, encoding="utf-8", errors="ignore").read()
            if len(text) > 5000 and any(k in text.lower() for k in keywords):
                rich.append(txt_path)
        except Exception:
            pass
        if len(rich) >= limit:
            break
    return rich

def parse_doc_id(folder_name):
    """Extract doc_id, date, court, case_num from folder name.
    Format: 2020-02-13-SC-FR-21-2019
    """
    parts = folder_name.split("-")
    if len(parts) < 4:
        return folder_name, "unknown", "SC", "unknown"
    date = f"{parts[0]}-{parts[1]}-{parts[2]}"
    rest = "-".join(parts[3:])
    # Detect court
    if "SC" in rest[:5]:  court = "SC"
    elif "CA" in rest[:5]: court = "CA"
    else: court = "SC"
    case_num = rest.replace("-", "/", 1).replace("-", "/", 1)
    return folder_name, date, court, case_num

def get_sha(base):
    """Try to read git SHA from the corpus directory."""
    git_head = os.path.join(base, "..", ".git", "HEAD")
    if os.path.exists(git_head):
        ref = open(git_head).read().strip()
        if ref.startswith("ref:"):
            ref_path = os.path.join(base, "..", ".git", ref.split(" ")[1])
            if os.path.exists(ref_path):
                return open(ref_path).read().strip()[:12]
    return "unknown"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="../lk_supreme_court_judgements/data",
                        help="Path to corpus data folder")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    init_db()
    sha = get_sha(args.corpus)
    print(f"Corpus SHA: {sha}")
    print(f"Finding {args.limit} treatment-rich documents...")

    txt_files = find_rich_docs(args.corpus, args.limit)
    print(f"Found {len(txt_files)} documents\n")

    ok, fail = 0, 0
    for txt_path in txt_files:
        folder = os.path.basename(os.path.dirname(txt_path))
        doc_id, date, court, case_num = parse_doc_id(folder)

        # Check for metadata JSON
        json_path = txt_path.replace("doc.txt", "doc.json")
        if os.path.exists(json_path):
            try:
                meta = json.load(open(json_path, encoding="utf-8", errors="ignore"))
                case_num = meta.get("num", case_num) or case_num
                date     = meta.get("date_str", date) or date
            except Exception:
                pass

        try:
            text = open(txt_path, encoding="utf-8", errors="ignore").read()
            record = ingest_document(text, doc_id, case_num, court, date, sha)
            cit_count = len(record["entities"]["citations"])
            jdg_count = len(record["entities"]["judges"])
            print(f"  ✓ {doc_id[:50]:<50} | {cit_count} citations | {jdg_count} judges")
            ok += 1
        except Exception as e:
            print(f"  ✗ {doc_id} — {e}")
            fail += 1

    print(f"\nDone. {ok} succeeded, {fail} failed.")
    print(f"JSON files → corpus/cases/")
    print(f"SQLite     → corpus/cases.db")

if __name__ == "__main__":
    main()