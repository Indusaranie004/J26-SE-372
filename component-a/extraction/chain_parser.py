import re

CHAIN_PATTERNS = [
    (re.compile(
        r'\b(WP|SP|CP|NP|EP|NW|NC|UVA|SAB|SB)'
        r'[/\\](HCCA|HCC|HCALT)'
        r'[/\\](\w+)'
        r'[/\\]([\d]+[/\\][\d]{2,4}(?:\([A-Z]+\))?)',
        re.IGNORECASE), "CA"),

    (re.compile(
        r'\bDC\s+(\w+(?:\s+\w+)?)\s*'
        r'(?:Case\s+No\.?[-:]+\s*)?'
        r'([A-Z]?[/\\]?[\d]+[/\\][\d]{2,4})',
        re.IGNORECASE), "DC"),

    (re.compile(
        r'\bCA\s*(?:No\.?\s*)?[/\\]?\s*([\d]+[/\\][\d]{2,4})',
        re.IGNORECASE), "CA"),

    (re.compile(
        r'\bHC\s*(?:No\.?\s*)?[/\\]\s*([\d]+[/\\][\d]{2,4})',
        re.IGNORECASE), "HC"),
]

def parse_chain_from_caption(caption_text):
    chain = []
    seen = set()
    seen_nums = set()

    for pattern, court_override in CHAIN_PATTERNS:
        for m in pattern.finditer(caption_text):
            full_match = m.group(0).strip()
            if full_match in seen:
                continue
            seen.add(full_match)

            court = court_override if court_override else "HC"

            if "DC" in full_match.upper()[:5]:
                court = "DC"
                place_m = re.search(
                    r'\bDC\s+(\w+)\s+(?:Case|No)',
                    full_match, re.IGNORECASE
                )
                place = place_m.group(1).strip() if place_m else None
            elif "HCCA" in full_match.upper():
                parts = full_match.split("/")
                place = parts[2] if len(parts) > 2 else None
            else:
                place = None

            base_num = re.search(r'(\d+[/\\]\d{2,4})', full_match)
            base_key = f"{court}-{base_num.group(1)}" if base_num else full_match

            if base_key in seen_nums:
                continue
            seen_nums.add(base_key)

            chain.append({
                "court":     court,
                "num":       full_match,
                "place":     place,
                "in_corpus": False,
                "source":    "caption"
            })

    return chain