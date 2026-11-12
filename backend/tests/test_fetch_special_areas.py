import json

from sqlalchemy import select

from app.models import RawDocument
from app.models.enums import ScrapeStatus
from app.scraping import fetch_special_areas


def sample_response():
    university = {
        "id": 1,
        "tags": {"name": "Test University", "amenity": "university"},
    }
    airport = {"id": 2, "tags": {"name": "Test Airport", "aeroway": "aerodrome"}}
    shop = {"id": 3, "tags": {"name": "Test Shop", "shop": "supermarket"}}
    return json.dumps({"elements": [university, airport, shop]}, indent=2)


def stored_documents(db, run):
    return db.scalars(
        select(RawDocument).where(RawDocument.scrape_run_id == run.id)
    ).all()


def test_successful_fetch_keeps_the_raw_response(db, monkeypatch):
    text = sample_response()
    monkeypatch.setattr(
        fetch_special_areas, "download", lambda: (text, "application/json")
    )

    run = fetch_special_areas.run_fetch(db)

    assert run.status == ScrapeStatus.SUCCEEDED
    assert run.rows_added == 2
    assert run.finished_at is not None
    documents = stored_documents(db, run)
    assert len(documents) == 1
    assert documents[0].content == text
    assert documents[0].source_url == fetch_special_areas.OVERPASS_URL


def test_failed_download_marks_the_run_failed(db, monkeypatch):
    def unreachable():
        raise OSError("server unreachable")

    monkeypatch.setattr(fetch_special_areas, "download", unreachable)

    run = fetch_special_areas.run_fetch(db)

    assert run.status == ScrapeStatus.FAILED
    assert "server unreachable" in run.error_message
    assert stored_documents(db, run) == []
