from app.core.config import settings
from app.intelligence.departments import department_for

FALLBACK_CATEGORY = "other"


def fuse_predictions(db, text_pred, image_pred):
    conflict = False

    if text_pred is None and image_pred is None:
        category = FALLBACK_CATEGORY
        confidence = 0.0
        source = None
    elif image_pred is None:
        category = text_pred["category"]
        confidence = text_pred["confidence"]
        source = "text"
    elif text_pred is None:
        category = image_pred["category"]
        confidence = image_pred["confidence"]
        source = "image"
    elif text_pred["category"] == image_pred["category"]:
        category = text_pred["category"]
        confidence = max(text_pred["confidence"], image_pred["confidence"])
        source = "both"
    else:
        conflict = True
        image_is_sure = image_pred["confidence"] >= settings.image_confidence_threshold
        if settings.image_wins_conflicts and image_is_sure:
            category = image_pred["category"]
            confidence = image_pred["confidence"]
            source = "image"
        else:
            category = text_pred["category"]
            confidence = text_pred["confidence"]
            source = "text"

    needs_review = conflict or confidence < settings.text_confidence_threshold
    department = department_for(db, category, confidence)

    return {
        "category": category,
        "confidence": confidence,
        "needs_review": needs_review,
        "source": source,
        "conflict": conflict,
        "department": department,
    }
