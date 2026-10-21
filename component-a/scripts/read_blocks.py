import json, os

def read_text_from_blocks(folder_path):
    """Extract full text from blocks.json."""
    blocks_path = os.path.join(folder_path, "blocks.json")
    if not os.path.exists(blocks_path):
        return None
    try:
        blocks = json.load(open(blocks_path, encoding="utf-8"))
        # Sort by page then bbox y position
        blocks.sort(key=lambda b: (b.get("page_number", 0), -b.get("bbox", [0,0,0,0])[3]))
        text = " ".join(b["text"] for b in blocks if b.get("text","").strip())
        return text if len(text) > 100 else None
    except Exception:
        return None