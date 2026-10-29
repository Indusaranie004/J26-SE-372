import re

# ── TREATMENT KEYWORD LISTS ───────────────────────────────────────

FOLLOWED_KW = [
    "followed", "applied", "approved", "affirmed", "adopted",
    "endorsed", "relied on", "relied upon", "as laid down in",
    "reaffirmed", "reiterated", "consistent with",
    "applied the principle", "followed the principle",
    "approved of", "endorsed the view"
]

DISTINGUISHED_KW = [
    "distinguished", "is distinguishable", "does not apply",
    "materially different", "confined to its own facts",
    "turned on its own facts", "on the facts of that case",
    "inapplicable", "not applicable", "factually distinguishable",
    "declined to extend", "limited to its own facts",
    "to be distinguished"
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
    "disagreed with", "expressed doubt",
    "with respect disagree", "hesitation in following",
    "not entirely satisfied", "reservations about"
]

# ── FIX 1: COUNSEL SUBMISSION FILTER ────────────────────────────
# These phrases indicate counsel is citing the case, not the court treating it

SUBMISSION_SIGNALS = [
    "counsel for", "learned counsel", "president's counsel",
    "relied on the judgment", "relied on the decision",
    "relied on the case", "submitted that", "contended that",
    "argued that", "on behalf of", "for the appellant",
    "for the respondent", "for the petitioner",
    "for the plaintiff", "for the defendant",
    "mr.", "mrs.", "ms.", "dr.",
]

# ── PROCEDURAL NOISE FILTER ───────────────────────────────────────

PROCEDURAL_SIGNALS = [
    "objection", "objections", "submission", "submissions",
    "preliminary objection", "preliminary issue", "motion",
    "the application was", "application is", "application was",
    "learned trial judge", "learned magistrate",
    "learned high court judge", "learned district judge",
    "learned additional", "the ruling", "the order",
    "interlocutory", "the decision below",
    "discussed in the cases", "discussed in the following",
    "mentioned in the cases", "referred to in the cases", "distinguished had been",
    "distinguished from contracts",
    "distinguished from each other",
    "must be distinguished from",
    ]

# ── FIX 2: VERB-AFTER-CITATION PATTERNS ─────────────────────────
# For followed/distinguished, the verb should come AFTER the citation
# These patterns confirm the court is doing the treating

ACTIVE_TREATMENT_RX = re.compile(
    r'\b('
    # Standard passive: was/were/has been followed/distinguished
    r'was\s+followed|were\s+followed|has\s+been\s+followed|'
    r'was\s+applied|were\s+applied|has\s+been\s+applied|'
    r'was\s+adopted|were\s+adopted|has\s+been\s+adopted|'
    r'was\s+approved|were\s+approved|has\s+been\s+approved|'
    r'was\s+affirmed|was\s+endorsed|'
    # Distinguished specific constructions
    r'was\s+distinguished|were\s+distinguished|'
    r'can\s+be\s+distinguished|could\s+be\s+distinguished|'
    r'may\s+be\s+distinguished|must\s+be\s+distinguished|'
    r'is\s+distinguishable|are\s+distinguishable|'
    r'cases?\s+(?:could|can|may)\s+be\s+distinguished|'
    # Overruled
    r'was\s+overruled|were\s+overruled|per\s+incuriam|'
    r'no\s+longer\s+good\s+law|wrongly\s+decided'
    r')\b',
    re.IGNORECASE
)

# ── DIRECTION ATTRIBUTION ─────────────────────────────────────────

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
    """Return True if procedural ruling — not a precedent treatment."""
    w = window.lower()
    return any(p in w for p in PROCEDURAL_SIGNALS)

def is_submission(window):
    """Return True if counsel submission — not a court treatment."""
    w = window.lower()
    return any(p in w for p in SUBMISSION_SIGNALS)

def has_active_treatment_verb(window):
    """Return True if window contains passive treatment verb pattern.
    e.g. 'was followed', 'were applied', 'has been distinguished'
    These confirm the court is treating, not just citing.
    """
    return bool(ACTIVE_TREATMENT_RX.search(window))

def verb_after_citation(body_text, citation_offset, window_end, max_dist=200):
    """
    FIX 2: Check whether the treatment verb appears AFTER the citation.
    For followed/distinguished, verb should come after the case name.
    """
    post_citation_text = body_text[citation_offset:citation_offset + max_dist]
    return bool(ACTIVE_TREATMENT_RX.search(post_citation_text))

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

def extract_window(body_text, char_offset, pre_chars=200, post_chars=200):
    """Extract text window around a citation — reduced from 300 to 200."""
    start = max(0, char_offset - pre_chars)
    end   = min(len(body_text), char_offset + post_chars)
    return body_text[start:end], start

def extract_treatments(body_text, current_doc_id, citations):
    """
    For each citation entity, extract the treatment relation.
    Applies three fixes:
    1. Submission filter — drops counsel citations
    2. Verb-after-citation — for followed/distinguished, verb must come after case name
    3. Proximity filter — treatment verb within 30 words of citation
    """
    results = []

    for citation in citations:
        cited_text  = citation["text"]
        body_offset = citation.get("body_offset", 0)

        window, win_start = extract_window(body_text, body_offset)

        # Classify
        treatment_type = classify_window(window)
        if treatment_type == "unclassified":
            continue

        # Filter 1 — procedural noise
        if is_procedural(window):
            continue

        # Filter 2 — counsel submission language
        if is_submission(window):
            continue

        # Filter 3 — for followed/distinguished require active verb pattern
        # This eliminates "cited in", "discussed in", "considered" etc.
        if treatment_type in ("followed", "distinguished"):
            if not has_active_treatment_verb(window):
                continue

        # Filter 4 — distinguished: verify a case citation is nearby the verb
        if treatment_type == "distinguished":
            verb_match = ACTIVE_TREATMENT_RX.search(window)
            if verb_match:
                verb_abs_pos = win_start + verb_match.start()
                nearby_cit = find_nearest_citation(
                    body_text, verb_abs_pos, "before", max_dist=200
                ) or find_nearest_citation(
                    body_text, verb_abs_pos, "after", max_dist=200
                )
                if not nearby_cit:
                    continue  # legal definition not case treatment

        # Filter 5 — FIX 2: for followed, verb should appear after citation
        if treatment_type == "followed":
            if not verb_after_citation(body_text, body_offset, body_offset + 300):
                # Check if verb appears in a reasonable window before too
                pre_window = body_text[max(0, body_offset-100):body_offset]
                if not ACTIVE_TREATMENT_RX.search(pre_window):
                    continue

        # Direction attribution
        treating = current_doc_id
        treated  = cited_text

        if PREDICATIVE_RX.search(window):
            treating = current_doc_id
            treated  = cited_text
        elif ACTIVE_TREATMENT_RX.search(window):
            verb_match = ACTIVE_TREATMENT_RX.search(window)
            if verb_match:
                verb_pos = win_start + verb_match.start()
                before_cit = find_nearest_citation(
                    body_text, verb_pos, "before"
                )
                if before_cit and before_cit.lower() != cited_text.lower():
                    treating = before_cit
                    treated  = cited_text

        # Evidence snippet
        ev_start = max(0, body_offset - 100)
        ev_end   = min(len(body_text), body_offset + 150)
        evidence = body_text[ev_start:ev_end].strip()

        results.append({
            "treating_doc_id":   treating,
            "treated_case_name": treated,
            "treatment_type":    treatment_type,
            "evidence":          evidence,
            "char_offset":       citation.get("start", body_offset)
        })

    return results