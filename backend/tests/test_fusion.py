import pytest

from app.core.config import settings
from app.intelligence.fusion import fuse_predictions
from app.seed import seed_departments


@pytest.fixture(autouse=True)
def fusion_settings(db, monkeypatch):
    monkeypatch.setattr(settings, "text_confidence_threshold", 0.5)
    monkeypatch.setattr(settings, "image_confidence_threshold", 0.4)
    monkeypatch.setattr(settings, "image_wins_conflicts", True)
    seed_departments(db)


def pred(category, confidence):
    return {"category": category, "confidence": confidence}


def test_text_only(db):
    result = fuse_predictions(db, pred("pothole", 0.8), None)

    assert result["category"] == "pothole"
    assert result["confidence"] == 0.8
    assert result["source"] == "text"
    assert result["conflict"] is False
    assert result["needs_review"] is False
    assert result["department"]["name"] == "Roads / Public Works"


def test_image_only(db):
    result = fuse_predictions(db, None, pred("garbage", 0.7))

    assert result["category"] == "garbage"
    assert result["source"] == "image"
    assert result["conflict"] is False
    assert result["department"]["name"] == "Sanitation / Solid Waste"


def test_both_agree_uses_higher_confidence(db):
    result = fuse_predictions(db, pred("pothole", 0.6), pred("pothole", 0.9))

    assert result["category"] == "pothole"
    assert result["confidence"] == 0.9
    assert result["source"] == "both"
    assert result["conflict"] is False
    assert result["needs_review"] is False


def test_conflict_image_wins_at_threshold(db):
    result = fuse_predictions(db, pred("pothole", 0.9), pred("garbage", 0.4))

    assert result["category"] == "garbage"
    assert result["source"] == "image"
    assert result["conflict"] is True
    assert result["needs_review"] is True


def test_conflict_text_stands_below_threshold(db):
    result = fuse_predictions(db, pred("pothole", 0.9), pred("garbage", 0.39))

    assert result["category"] == "pothole"
    assert result["source"] == "text"
    assert result["conflict"] is True
    assert result["needs_review"] is True


def test_neither_input_goes_to_other_for_review(db):
    result = fuse_predictions(db, None, None)

    assert result["category"] == "other"
    assert result["source"] is None
    assert result["needs_review"] is True
    assert result["department"]["name"] == "General Grievance"


def test_review_flag_follows_the_confidence_threshold(db):
    at_threshold = fuse_predictions(db, pred("pothole", 0.5), None)
    below_threshold = fuse_predictions(db, pred("pothole", 0.49), None)

    assert at_threshold["needs_review"] is False
    assert below_threshold["needs_review"] is True
