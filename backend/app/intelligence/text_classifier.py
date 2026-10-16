import re
from functools import lru_cache

import joblib

from app.core.config import settings

FALLBACK_CATEGORY = "other"
TOP_K = 3


@lru_cache(maxsize=1)
def load_text_model():
    return joblib.load(settings.text_model_file)


def classify_text(text, threshold=None):
    if threshold is None:
        threshold = settings.text_confidence_threshold

    if not text or not re.search(r"\w", text):
        return {
            "category": FALLBACK_CATEGORY,
            "confidence": 0.0,
            "top_k": [],
            "needs_review": True,
        }

    model = load_text_model()
    probs = model.predict_proba([text])[0]
    ranked = sorted(
        zip(model.classes_, probs, strict=True), key=lambda p: p[1], reverse=True
    )
    top_k = [
        {"category": str(name), "confidence": round(float(p), 4)}
        for name, p in ranked[:TOP_K]
    ]

    best = top_k[0]
    unsure = best["confidence"] < threshold
    return {
        "category": FALLBACK_CATEGORY if unsure else best["category"],
        "confidence": best["confidence"],
        "top_k": top_k,
        "needs_review": unsure,
    }
