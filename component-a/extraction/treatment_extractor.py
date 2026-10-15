import re

# ── TREATMENT KEYWORD LISTS ───────────────────────────────────────

FOLLOWED_KW = [
    "followed", "applied", "approved", "affirmed", "adopted",
    "endorsed", "relied on", "relied upon", "as laid down in",
    "reaffirmed", "reiterated", "consistent with", "in accordance with",
    "applied the principle", "followed the principle"
]

DISTINGUISHED_KW = [
    "distinguished", "is distinguishable", "does not apply",
    "materially different", "confined to its own facts",
    "turned on its own facts", "on the facts of that case",
    "inapplicable", "not applicable", "factually distinguishable",
    "declined to extend", "limited to its own facts"
]

NEGATIVE_KW = [
    "overruled", "overrule", "overruling",
    "no longer good law", "wrongly decided",
    "per incuriam", "unable to agree with",
    "decline to follow", "declined to follow",
    "not followed", "must be reconsidered",
    "cannot be supported", "fell into error",
    "not good law", "bad law"
]

DOUBTED_KW = [
    "doubted", "questioned", "called into doubt",
    "disagreed with", "not sure", "expressed doubt",
    "with respect disagree", "hesitation in following"
]

# ── PROCEDURAL NOISE FILTER ───────────────────────────────────────
# "overruled the objection" is NOT a precedent treatment

PROCEDURAL_SIGNALS = [
    "objection", "objections", "submission", "submissions",
    "preliminary objection", "preliminary issue", "motion",
    "the application was", "application is", "application was",
    "learned trial judge", "learned magistrate",
    "learned high court judge", "learned district judge",
    "learned additional", "the ruling", "the order",
    "interlocutory", "the decision below"
]

# ── DIRECTION ATTRIBUTION ─────────────────────────────────────────
# Active:      "A overruled B"  → A is treating, B is treated
# Predicative: "B is per incuriam" → current case is treating, B is treated

ACTIVE_RX = re.compile(
    r'\b(overrul\w+|declin\w+\s+to\s+follow|not\s+follow\w+|'
    r'distinguish\w+)\b',
    re.IGNORECASE
)

PREDICATIVE_RX = re.compile(
    r'\b(per\s+incuriam|wrongly\s+decided|cannot\s+be\s+supported|'
    r'no\s+longer\s+good\s+law|not\s+good\s+law)\b',
    re.IGNORECASE
)

CITATION_RX = re.compile(
    r'\b([A-Z][A-Za-z.\-\']*'
    r'(?:\s+(?:[A-Z][A-Za-z.\-\']*|of|the|and)){0,4}'
    r'\s+[Vv][Ss]?\.?\s+'
    r'[A-Z][A-Za-z.\-\']*'
    r'(?:\s+(?:[A-Z][A-Za-z.\-\']*|of|the|and)){0,4})'
)

def classify_window(window):
    """Classify treatment type from surrounding text."""
    w = window.lower()
    if any(k in w for k in NEGATIVE_KW):
        return "overruled"
    if any(k in w for k in DISTINGUISHED_KW):
        return "distinguished"
    if any(k in w for k in DOUBTED_KW):
        return "doubted"
    if any(k in w for k in FOLLOWED_KW):
        return "followed"
    return "unclassified"

def is_procedural(window):
    """Return True if the treatment verb refers to a procedural ruling."""
    w = window.lower()
    return any(p in w for p in PROCEDURAL_SIGNALS)

def find_nearest_citation(text, pos, direction, max_dist=300):
    """Find nearest citation before or after position pos."""
    best = None
    for m in CITATION_RX.finditer(text):
        if direction == "before":
            if m.end() <= pos and (pos - m.end()) < max_dist:
                if best is None or m.end() > best[0]:
                    best = (m.end(), m.group(1).strip())
        else:
            if m.start() >= pos and (m.start() - pos) < max_dist:
                if best is None or m.start() < best[0]:
                    best = (m.start(), m.group(1).strip())
    return best[1] if best else None

def extract_window(body_text, char_offset, pre_chars=300, post_chars=300):
    """Extract text window around a citation."""
    start = max(0, char_offset - pre_chars)
    end   = min(len(body_text), char_offset + post_chars)
    return body_text[start:end], start

def extract_treatments(body_text, current_doc_id, citations):
    """
    For each citation entity, extract the treatment relation.
    Returns list of dicts with treating, treated, type, evidence, offset.
    """
    results = []

    for citation in citations:
        cited_text   = citation["text"]
        # char_offset is relative to full document — body starts at body char_start
        # we need the offset within body_text
        body_offset  = citation.get("body_offset", 0)

        window, win_start = extract_window(body_text, body_offset)

        # Classify
        treatment_type = classify_window(window)
        if treatment_type == "unclassified":
            continue

        # Procedural noise filter
        if is_procedural(window):
            continue

        # Direction attribution
        treating = current_doc_id
        treated  = cited_text

        if ACTIVE_RX.search(window):
            # "A overruled B" — find if another citation appears before the verb
            verb_match = ACTIVE_RX.search(window)
            if verb_match:
                verb_pos_in_window = win_start + verb_match.start()
                before_citation = find_nearest_citation(
                    body_text, verb_pos_in_window, "before"
                )
                if before_citation and before_citation.lower() != cited_text.lower():
                    # A third case is doing the overruling
                    treating = before_citation
                    treated  = cited_text

        elif PREDICATIVE_RX.search(window):
            # "B is per incuriam" — current case is treating, B is treated
            treating = current_doc_id
            treated  = cited_text

        # Evidence snippet — verbatim 200 chars around the citation
        ev_start = max(0, body_offset - 100)
        ev_end   = min(len(body_text), body_offset + 100)
        evidence = body_text[ev_start:ev_end].strip()

        results.append({
            "treating_doc_id":  treating,
            "treated_case_name": treated,
            "treatment_type":    treatment_type,
            "evidence":          evidence,
            "char_offset":       citation.get("start", body_offset)
        })

    return results