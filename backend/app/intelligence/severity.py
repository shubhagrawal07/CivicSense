import json
import re

from app.core.config import ROOT_DIR
from app.models.enums import Severity

LEVELS = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
FALLBACK_CATEGORY = "other"
POINTS_PER_LEVEL = 25

_rules = json.loads(
    (ROOT_DIR / "shared" / "severity_rules.json").read_text(encoding="utf-8")
)
CATEGORY_DEFAULTS = {k: Severity(v) for k, v in _rules["category_defaults"].items()}
KEYWORDS = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _rules["boost_keywords"]) + r")\b",
    re.IGNORECASE,
)


def _result(level, reasons):
    score = (LEVELS.index(level) + 1) * POINTS_PER_LEVEL
    return {"level": level, "score": score, "reasons": reasons}


def compute_severity(category, description, has_image):
    if not has_image:
        return _result(Severity.LOW, ["no photo evidence"])

    if category not in CATEGORY_DEFAULTS:
        category = FALLBACK_CATEGORY
    level = CATEGORY_DEFAULTS[category]
    reasons = [f"photo attached, {category} defaults to {level.value}"]

    found = list(dict.fromkeys(m.lower() for m in KEYWORDS.findall(description or "")))
    if found:
        words = ", ".join(found)
        raised = LEVELS[min(LEVELS.index(level) + 1, len(LEVELS) - 1)]
        if raised == level:
            reasons.append(f"safety words ({words}) found, already at {level.value}")
        else:
            reasons.append(
                f"safety words ({words}) raise it from {level.value} to {raised.value}"
            )
        level = raised

    return _result(level, reasons)
