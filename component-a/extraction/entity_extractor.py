import re
from .segmentation import segment

STOP_LEAD  = {"in","see","the","and","also","vide","per","cf","re",
               "of","at","held","that","case","following","said"}
STOP_TRAIL = {"see","the","in","it","this","held","at","however",
               "but","further","therefore","accordingly","thus","page"}

CASE_NUM_RX = re.compile(
    r'\b(SC[\s/\\]+(?:APPEAL|FR|CHC|SPL|MISC|LA|HC|TAB)?'
    r'[\s/\\]*[\d]+[\s/\\][\d]{2,4}|'
    r'CA[\s/\\]+(?:DC|HC|PHC|WRIT|APN|REV)?[\s/\\]*[\d]+[\s/\\][\d]{2,4}|'
    r'(?:HC|DC|MC)[\s/\\]+\w+[\s/\\]*[\d]+[\s/\\][\d]{2,4})',
    re.IGNORECASE
)

JUDGE_RX = re.compile(
    r'([A-Z][A-Z.]{1,6}(?:\.[A-Z]+)*(?:\s+[A-Z][A-Z.]*)*)'  # name with initials
    r'\s*,?\s*'
    r'(?:and\s+)?'
    r'(C\.?J\.?|J\.S\.C\.?|J\.?)\b',
    re.MULTILINE
)

COUNSEL_RX = re.compile(
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})'
    r'\s+(?:P\.?C\.?|A\.?A\.?L\.?|'
    r'(?:Senior\s+)?(?:Deputy\s+)?(?:Additional\s+)?'
    r'(?:Solicitor|Attorney)\s+General)',
)

ACT_RX = re.compile(
    r'\b((?:[A-Z][\w\'\-]+\s+){1,7}(?:Act|Ordinance|Code|Law))'
    r'(?:[\s,]*No\.?\s*(\d+)\s+of\s+(\d{4}))?'
    r'(?:[,\s]*[Ss](?:ection|\.)\s*(\w+))?'
)

CITATION_RX = re.compile(
    r'\b([A-Z][A-Za-z.\-\']*'
    r'(?:\s+(?:[A-Z][A-Za-z.\-\']*|of|the|and)){0,4}'
    r'\s+[Vv][Ss]?\.?\s+'
    r'[A-Z][A-Za-z.\-\']*'
    r'(?:\s+(?:[A-Z][A-Za-z.\-\']*|of|the|and)){0,4})'
)

ACT_STOP = {"the court","this court","supreme court",
            "appeal court","high court","district court"}

def clean_citation(s):
    s = re.sub(r'\s+', ' ', s).strip(" .,;:")
    t = s.split()
    while t and t[0].lower().strip(".,") in STOP_LEAD:  t.pop(0)
    while t and t[-1].lower().strip(".,") in STOP_TRAIL: t.pop()
    s = " ".join(t).strip(" .,;:")
    return s if " v" in s.lower() and len(s) > 6 else None

def extract_entities(text):
    sections = segment(text)
    entities = []

    # Case numbers — caption only
    for m in CASE_NUM_RX.finditer(sections["caption"]["text"]):
        entities.append({
            "label": "CASE_NUMBER",
            "text": m.group(1).strip(),
            "start": sections["caption"]["char_start"] + m.start(),
            "end":   sections["caption"]["char_start"] + m.end()
        })

    # Judges — header section (now contains BEFORE:- block)
    seen_judges = set()
    header_text = sections["header"]["text"]
    for m in JUDGE_RX.finditer(header_text):
        name = m.group(1).strip(" ,.\n")
        name = re.sub(r'\s+', ' ', name).strip()
        # Must have at least one space or dot — filter single initials
        if len(name) > 5 and ('.' in name or ' ' in name) and name not in seen_judges:
            seen_judges.add(name)
            entities.append({
                "label": "JUDGE",
                "text":  name,
                "start": sections["header"]["char_start"] + m.start(),
                "end":   sections["header"]["char_start"] + m.end()
            })

    # Counsel — header only
    seen_counsel = set()
    for m in COUNSEL_RX.finditer(sections["header"]["text"]):
        name = m.group(1).strip()
        if name not in seen_counsel:
            seen_counsel.add(name)
            entities.append({
                "label": "COUNSEL",
                "text": name,
                "start": sections["header"]["char_start"] + m.start(),
                "end":   sections["header"]["char_start"] + m.end()
            })

    # Acts — body only
    seen_acts = set()
    for m in ACT_RX.finditer(sections["body"]["text"]):
        name = re.sub(r'\s+', ' ', m.group(1)).strip()
        if len(name.split()) >= 2 and name.lower() not in ACT_STOP \
                and name not in seen_acts:
            seen_acts.add(name)
            entities.append({
                "label":      "ACT",
                "text":       name,
                "act_number": m.group(2),
                "act_year":   m.group(3),
                "section":    m.group(4),
                "start": sections["body"]["char_start"] + m.start(),
                "end":   sections["body"]["char_start"] + m.end()
            })

    # Citations — body only
    seen_cit = set()
    for m in CITATION_RX.finditer(sections["body"]["text"]):
        cleaned = clean_citation(m.group(1))
        if cleaned and cleaned not in seen_cit:
            seen_cit.add(cleaned)
            entities.append({
                "label": "CITATION",
                "text":  cleaned,
                "start": sections["body"]["char_start"] + m.start(),
                "end":   sections["body"]["char_start"] + m.end()
            })

    return sections, entities