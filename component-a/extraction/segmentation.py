import re

CONCLUSION_TRIGGERS = [
    "for the foregoing reasons",
    "accordingly we hold",
    "we therefore order",
    "in the result",
    "the appeal is dismissed",
    "the appeal is allowed",
    "the application is dismissed",
    "the application is allowed",
    "we make order",
    "order accordingly",
    "i would therefore",
    "we would therefore",
    "the petition is dismissed",
    "the petition is allowed",
]

# Matches SC/FR/527/2011 style and variants
CAPTION_RX = re.compile(
    r'\b(SC[\s./\\]+(?:FR|APPEAL|CHC|SPL|HC|MISC|TAB|LA)?'
    r'[\s./\\]*[\d]+[\s./\\][\d]{2,4}|'
    r'CA[\s./\\]+(?:DC|HC|PHC|WRIT|APN)?[\s./\\]*[\d]+[\s./\\][\d]{2,4}|'
    r'(?:HC|DC|MC)[\s./\\]+\w+[\s./\\]*[\d]+[\s./\\][\d]{2,4})',
    re.IGNORECASE
)

# Detects the BEFORE:- block which marks start of header
BEFORE_RX = re.compile(r'\bBEFORE\s*:-?\s*', re.IGNORECASE)

# Detects ARGUED ON / DECIDED ON which marks end of header
ARGUED_RX = re.compile(
    r'\b(?:ARGUED\s+ON|Argued\s+On|DECIDED\s+ON|Decided\s+On)'
    r'\s*:-?\s*\d',
    re.IGNORECASE
)

def segment(text):
    # ── CAPTION ──────────────────────────────────────────────────
    # Find the BEFORE:- marker — everything before it is caption
    before_match = BEFORE_RX.search(text[:8000])
    if before_match:
        caption_end = before_match.start()
    else:
        # Fallback: last case number in first 3000 chars
        head = text[:3000]
        matches = list(CAPTION_RX.finditer(head))
        if matches:
            caption_end = matches[-1].end()
            nl = text.find('\n', caption_end)
            caption_end = nl if nl > 0 else caption_end + 200
        else:
            caption_end = min(800, len(text))

    # ── HEADER ───────────────────────────────────────────────────
    # Header starts at BEFORE:- and ends after ARGUED ON / DECIDED ON
    header_start = caption_end
    argued_match = ARGUED_RX.search(text, caption_end, caption_end + 3000)
    if argued_match:
        # Extend to end of that line
        nl = text.find('\n', argued_match.end())
        header_end = nl if nl > 0 else argued_match.end() + 50
    else:
        # No ARGUED ON found — use first long paragraph after caption
        header_end = caption_end
        pos = caption_end
        while pos < min(caption_end + 4000, len(text)):
            nl = text.find('\n', pos)
            if nl == -1:
                break
            para = text[nl+1:nl+300].strip()
            if len(para) > 150 and not CAPTION_RX.search(para[:100]):
                header_end = nl
                break
            pos = nl + 1

    # ── CONCLUSION ───────────────────────────────────────────────
    conclusion_start = len(text)
    search_from = int(len(text) * 0.60)
    for trigger in CONCLUSION_TRIGGERS:
        idx = text.lower().find(trigger, search_from)
        if idx != -1 and idx < conclusion_start:
            conclusion_start = idx

    return {
        "caption": {
            "text":       text[:caption_end].strip(),
            "char_start": 0,
            "char_end":   caption_end
        },
        "header": {
            "text":       text[header_start:header_end].strip(),
            "char_start": header_start,
            "char_end":   header_end
        },
        "body": {
            "text":       text[header_end:conclusion_start].strip(),
            "char_start": header_end,
            "char_end":   conclusion_start
        },
        "conclusion": {
            "text":       text[conclusion_start:].strip(),
            "char_start": conclusion_start,
            "char_end":   len(text)
        }
    }