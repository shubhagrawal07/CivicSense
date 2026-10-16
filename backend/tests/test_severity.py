import json

from app.core.config import ROOT_DIR
from app.intelligence.severity import compute_severity
from app.models.enums import Severity

taxonomy = json.loads((ROOT_DIR / "shared" / "categories.json").read_text())
category_keys = [c["key"] for c in taxonomy["categories"]]

EXPECTED_DEFAULTS = {
    "open_manhole": Severity.HIGH,
    "electricity_outage": Severity.HIGH,
    "pothole": Severity.MEDIUM,
    "drainage_sewage": Severity.MEDIUM,
    "water_leakage": Severity.MEDIUM,
    "road_obstruction": Severity.MEDIUM,
    "streetlight": Severity.LOW,
    "garbage": Severity.LOW,
    "damaged_infrastructure": Severity.LOW,
    "other": Severity.LOW,
}


def test_report_without_a_photo_is_always_low():
    result = compute_severity("open_manhole", "child fell in, live wire nearby", False)

    assert result["level"] == Severity.LOW
    assert result["reasons"] == ["no photo evidence"]


def test_every_category_has_its_default_with_a_photo():
    assert set(EXPECTED_DEFAULTS) == set(category_keys)
    for category, expected in EXPECTED_DEFAULTS.items():
        result = compute_severity(category, None, True)
        assert result["level"] == expected, category
        assert result["reasons"], category


def test_safety_words_raise_one_level_and_stop_at_critical():
    plain = compute_severity("pothole", "big pothole on the main road", True)
    boosted = compute_severity("pothole", "Big pothole next to a SCHOOL gate", True)
    assert plain["level"] == Severity.MEDIUM
    assert boosted["level"] == Severity.HIGH
    assert boosted["score"] > plain["score"]
    assert "school" in boosted["reasons"][-1]

    many = compute_severity("open_manhole", "child hurt in an accident at school", True)
    assert many["level"] == Severity.CRITICAL

    assert compute_severity("pothole", "preschool kitchen nearby", True)["level"] == (
        Severity.MEDIUM
    )
