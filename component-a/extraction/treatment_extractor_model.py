import os

# ── Lazy model loader ─────────────────────────────────────────────
_classifier = None

LABEL_MAP = {
    "LABEL_0": "followed",
    "LABEL_1": "distinguished",
    "LABEL_2": "overruled",
    "LABEL_3": "doubted",
    "LABEL_4": "none"
}

def get_classifier():
    global _classifier
    if _classifier is not None:
        return _classifier
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "model", "treatment_classifier"
    )
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path} — falling back to rule-based")
        return None
    try:
        from transformers import pipeline as hf_pipeline
        _classifier = hf_pipeline(
            "text-classification",
            model=model_path,
            tokenizer=model_path,
            device=-1  # CPU
        )
        print("InLegalBERT classifier loaded.")
        return _classifier
    except Exception as e:
        print(f"Model load failed: {e} — falling back to rule-based")
        return None

LABEL_THRESHOLDS = {
        "followed":      0.80,
        "distinguished": 0.85,
        "overruled":     0.92,
        "doubted":       0.92,
        "none":          0.50
    }

def extract_treatments_model(body_text, current_doc_id, citations):
    """
    Model-based treatment extraction using fine-tuned InLegalBERT.
    Falls back to rule-based extractor if model is unavailable.
    """
    
    from extraction.treatment_extractor import extract_treatments

    classifier = get_classifier()
    if classifier is None:
        return extract_treatments(body_text, current_doc_id, citations)

    results = []
    seen = set()

    for citation in citations:
        offset = citation.get("body_offset", citation.get("start", 0))
        start  = max(0, offset - 300)
        end    = min(len(body_text), offset + 300)
        window = body_text[start:end].strip()

        if len(window) < 20:
            continue

        try:
            pred  = classifier(window[:512])[0]
            label = LABEL_MAP.get(pred["label"], pred["label"])
            score = pred["score"]

            label_threshold = LABEL_THRESHOLDS.get(label, 0.80)
            if label == "none" or score < label_threshold:
                continue

            # Deduplicate — same case + same label within same doc
            key = (citation["text"].lower()[:50], label)
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "treated_case_name": citation["text"],
                "treatment_type":    label,
                "evidence":          window,
                "char_offset":       offset,
                "confidence":        round(score, 3),
                "method":            "model"
            })
        except Exception:
            continue

    return results