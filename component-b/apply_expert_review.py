"""Convert the lawyer's GT_Expert_Review_20.xlsx into gt1_expert.json and gt2_expert.json."""
import json, openpyxl

GT1_IN = "data/gt1_queries.json"

SHEET, GT2_IN = "data/GT_Expert_Review_20.xlsx", "data/gt2_clean.json"

ws = openpyxl.load_workbook(SHEET)["Review"]
ok = set()          # (case_id, level, item) marked Correct
fit = {}            # query -> [case_ids] whose Precedent row is marked Correct
cases = set()
for r in ws.iter_rows(min_row=11, values_only=True):
    item, mark, level, case, query = r[2], r[4], r[6], r[7], r[8]
    if not case: continue
    cases.add(case)
    if mark == "Correct":
        ok.add((case, level, item))
        if level == "Precedent": fit.setdefault(query, []).append(case)

def act(a):
    return a["act_name"] + (f" ({a['year']})" if a["year"] else "") + (f", s. {a['section']}" if a["section"] else "")
def lit(l):
    return f"{l['case_num']} ({l['court']} {l['place'] or ''})".replace(" )", ")")

orig = {g["query"]: g for g in json.load(open(GT1_IN, encoding="utf-8"))}   # keep original intent/split
gt1 = [{"query": q, "relevant_ids": cs,
        "intent": orig.get(q, {}).get("intent"), "split": orig.get(q, {}).get("split")} for q, cs in fit.items()]
gt2 = []
for e in json.load(open(GT2_IN, encoding="utf-8")):
    c = e["seed_id"]
    if c not in cases: continue                      # keep all 20 seeds (oracle seeds)
    x = e["expected"]
    gt2.append({**e, "split": "expert", "expected": {
        "litigation_history":     [l for l in x["litigation_history"]     if (c, "Litigation", lit(l)) in ok],
        "legislative_foundation": [a for a in x["legislative_foundation"] if (c, "Legislation", act(a)) in ok],
        "judicial_treatment":     [j for j in x["judicial_treatment"]     if (c, "Judicial Treatment", j["cited_name"]) in ok]}})

json.dump(gt1, open("data/gt1_expert.json", "w", encoding="utf-8"), indent=2)
json.dump(gt2, open("data/gt2_expert.json", "w", encoding="utf-8"), indent=2)
n_links = sum(len(v) for e in gt2 for v in e["expected"].values())
print(f"GT1: {len(gt1)} queries kept, {sum(len(g['relevant_ids']) for g in gt1)} precedents confirmed | GT2: {len(gt2)} seeds, {n_links} confirmed links")