import base64
import json
from functools import lru_cache
from pathlib import Path

import anthropic
from PIL import Image, UnidentifiedImageError

from app.core.config import ROOT_DIR, settings

_CATEGORIES = json.loads(
    (ROOT_DIR / "shared" / "categories.json").read_text(encoding="utf-8")
)
VALID_CATEGORIES = [c["key"] for c in _CATEGORIES["categories"]]
FALLBACK_CATEGORY = _CATEGORIES["fallback"]

_MEDIA_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": VALID_CATEGORIES},
        "confidence": {"type": "number"},
    },
    "required": ["category", "confidence"],
    "additionalProperties": False,
}


def _category_block():
    lines = []
    for c in _CATEGORIES["categories"]:
        subs = ", ".join(s["label"].lower() for s in c.get("subcategories", []))
        lines.append(f"- {c['key']}: {c['label']}" + (f" ({subs})" if subs else ""))
    return "\n".join(lines)


# built from shared/categories.json so it can't drift out of sync with the list
PROMPT = f"""You're classifying a photo a citizen submitted reporting a civic
infrastructure issue. Pick exactly one category from this list that best
matches what the photo shows:
{_category_block()}

If the photo is ambiguous, low quality, doesn't clearly match one category
over another, or isn't a civic issue at all, choose `other` rather than
guessing. Base your confidence on how clearly the photo matches. A blurry,
partial, or ambiguous photo should get a lower score even if you lean toward
a category. Don't default to high confidence.
Ignore people, vehicles, and background details that aren't the reported
issue itself."""


def _fallback(reason):
    return {
        "category": FALLBACK_CATEGORY,
        "confidence": 0.0,
        "raw_response": reason,
        "needs_review": True,
    }


@lru_cache(maxsize=1)
def _client():
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _call_claude(image_bytes, media_type):
    # split out on its own so tests can monkeypatch the network call without
    # touching the SDK client or faking a response object
    response = _client().messages.create(
        model=settings.image_classifier_model,
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.standard_b64encode(image_bytes).decode(),
                        },
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
        output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def classify_image(image_path):
    path = Path(image_path)
    media_type = _MEDIA_TYPES.get(path.suffix.lower())
    if media_type is None:
        return _fallback(f"unsupported file type: {path.suffix}")

    try:
        # catches corrupt/truncated files before we spend an API call on them
        with Image.open(path) as img:
            img.verify()
        image_bytes = path.read_bytes()
    except (UnidentifiedImageError, OSError) as e:
        return _fallback(f"unreadable image: {e}")

    try:
        result = _call_claude(image_bytes, media_type)
    except (anthropic.APIConnectionError, anthropic.APIStatusError) as e:
        return _fallback(f"claude api error: {e}")
    except Exception as e:  # schema/SDK surprises we didn't anticipate
        return _fallback(f"unexpected error: {e}")

    category = result.get("category")
    if category not in VALID_CATEGORIES:
        return _fallback(f"model returned an unknown category: {category!r}")

    confidence = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
    return {
        "category": category,
        "confidence": confidence,
        "raw_response": result,
        "needs_review": False,
    }
