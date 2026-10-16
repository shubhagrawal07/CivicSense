import pytest

from app.intelligence.text_classifier import classify_text


def test_clear_complaint_gets_its_category():
    result = classify_text("Deep pothole on the main road, two bikes have skidded")
    assert result["category"] == "pothole"
    assert result["needs_review"] is False
    assert result["confidence"] == result["top_k"][0]["confidence"]


def test_top_k_is_sorted_and_is_a_distribution_slice():
    top_k = classify_text("streetlight not working since last week")["top_k"]
    scores = [t["confidence"] for t in top_k]
    assert len(top_k) == 3
    assert scores == sorted(scores, reverse=True)
    assert sum(scores) <= 1.0001


@pytest.mark.parametrize("text", ["", "   ", "???", None])
def test_empty_text_is_flagged(text):
    result = classify_text(text)
    assert result["category"] == "other"
    assert result["needs_review"] is True
    assert result["top_k"] == []


def test_low_confidence_falls_back_to_other():
    result = classify_text("Deep pothole on the main road", threshold=1.01)
    assert result["needs_review"] is True
    assert result["category"] == "other"
    assert result["top_k"][0]["category"] == "pothole"


def test_threshold_is_configurable():
    text = "Deep pothole on the main road"
    assert classify_text(text, threshold=0.0)["needs_review"] is False
