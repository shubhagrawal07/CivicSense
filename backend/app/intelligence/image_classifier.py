import base64
import json
from functools import lru_cache
from pathlib import Path

import anthropic
from PIL import Image, UnidentifiedImageError

from app.core.config import ROOT_DIR, settings

categories_file = ROOT_DIR / "shared" / "categories.json"
CATEGORIES = json.loads(categories_file.read_text(encoding="utf-8"))
VALID_CATEGORIES = [c["key"] for c in CATEGORIES["categories"]]
FALLBACK_CATEGORY = CATEGORIES["fallback"]

MEDIA_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": VALID_CATEGORIES},
        "confidence": {"type": "number"},
    },
    "required": ["category", "confidence"],
    "additionalProperties": False,
}


def category_list():
    lines = []
    for category in CATEGORIES["categories"]:
        line = f"- {category['key']}: {category['label']}"
        labels = [s["label"].lower() for s in category.get("subcategories", [])]
        if labels:
            line += " (" + ", ".join(labels) + ")"
        lines.append(line)
    return "\n".join(lines)


PROMPT = f"""You're classifying a photo a citizen submitted reporting a civic
infrastructure issue. Pick exactly one category from this list that best
matches what the photo shows:
{category_list()}

If the photo is ambiguous, low quality, doesn't clearly match one category
over another, or isn't a civic issue at all, choose `other` rather than
guessing. Base your confidence on how clearly the photo matches. A blurry,
partial, or ambiguous photo should get a lower score even if you lean toward
a category. Don't default to high confidence.
Ignore people, vehicles, and background details that aren't the reported
issue itself."""


def fallback(reason):
    return {
        "category": FALLBACK_CATEGORY,
        "confidence": 0.0,
        "raw_response": reason,
        "needs_review": True,
    }


@lru_cache(maxsize=1)
def get_client():
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def call_claude(image_bytes, media_type):
    image_data = base64.standard_b64encode(image_bytes).decode()
    image_part = {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": image_data},
    }
    text_part = {"type": "text", "text": PROMPT}

    response = get_client().messages.create(
        model=settings.image_classifier_model,
        max_tokens=256,
        messages=[{"role": "user", "content": [image_part, text_part]}],
        output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
    )

    for block in response.content:
        if block.type == "text":
            return json.loads(block.text)
    raise ValueError("no text in response")


def classify_image(image_path):
    path = Path(image_path)
    media_type = MEDIA_TYPES.get(path.suffix.lower())
    if media_type is None:
        return fallback(f"unsupported file type: {path.suffix}")

    try:
        with Image.open(path) as image:
            image.verify()
        image_bytes = path.read_bytes()
    except (UnidentifiedImageError, OSError) as error:
        return fallback(f"unreadable image: {error}")

    try:
        result = call_claude(image_bytes, media_type)
    except (anthropic.APIConnectionError, anthropic.APIStatusError) as error:
        return fallback(f"claude api error: {error}")
    except Exception as error:
        return fallback(f"unexpected error: {error}")

    category = result.get("category")
    if category not in VALID_CATEGORIES:
        return fallback(f"model returned an unknown category: {category!r}")

    confidence = float(result.get("confidence", 0.0))
    confidence = max(0.0, min(1.0, confidence))
    return {
        "category": category,
        "confidence": confidence,
        "raw_response": result,
        "needs_review": False,
    }
