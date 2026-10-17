from PIL import Image

from app.intelligence import image_classifier
from app.intelligence.image_classifier import classify_image


def _make_image(path):
    Image.new("RGB", (10, 10)).save(path)


def test_valid_image_returns_the_mocked_category(tmp_path, monkeypatch):
    monkeypatch.setattr(
        image_classifier,
        "_call_claude",
        lambda *a, **k: {"category": "pothole", "confidence": 0.9},
    )
    path = tmp_path / "photo.png"
    _make_image(path)

    result = classify_image(path)

    assert result["category"] == "pothole"
    assert result["confidence"] == 0.9
    assert result["needs_review"] is False


def test_corrupt_image_falls_back_without_calling_claude(tmp_path, monkeypatch):
    def _should_not_be_called(*a, **k):
        raise AssertionError("an unreadable image should never reach the API call")

    monkeypatch.setattr(image_classifier, "_call_claude", _should_not_be_called)
    path = tmp_path / "broken.jpg"
    path.write_bytes(b"not actually an image")

    result = classify_image(path)

    assert result["category"] == "other"
    assert result["needs_review"] is True


def test_api_failure_falls_back_instead_of_raising(tmp_path, monkeypatch):
    def _raise(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(image_classifier, "_call_claude", _raise)
    path = tmp_path / "photo.png"
    _make_image(path)

    result = classify_image(path)

    assert result["category"] == "other"
    assert result["needs_review"] is True


def test_unknown_category_from_model_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr(
        image_classifier,
        "_call_claude",
        lambda *a, **k: {"category": "not_a_real_category", "confidence": 0.9},
    )
    path = tmp_path / "photo.png"
    _make_image(path)

    result = classify_image(path)

    assert result["category"] == "other"
    assert result["needs_review"] is True
