import json

from sqlalchemy import select

from app.models import RawDocument
from app.models.enums import ScrapeStatus
from app.scraping import fetch_boundaries


def sample_response():
    district = {"id": 1, "tags": {"name": "Mumbai City District", "admin_level": "5"}}
    ward_a = {"id": 2, "tags": {"name": "A Ward", "admin_level": "10"}}
    ward_b = {"id": 3, "tags": {"name": "B Ward", "admin_level": "10"}}
    return json.dumps({"elements": [district, ward_a, ward_b]}, indent=2)


def stored_documents(db, run):
    return db.scalars(
        select(RawDocument).where(RawDocument.scrape_run_id == run.id)
    ).all()


def test_successful_fetch_keeps_the_raw_response(db, monkeypatch):
    text = sample_response()
    monkeypatch.setattr(
        fetch_boundaries, "download", lambda: (text, "application/json")
    )

    run = fetch_boundaries.run_fetch(db)

    assert run.status == ScrapeStatus.SUCCEEDED
    assert run.rows_added == 2
    assert run.finished_at is not None
    documents = stored_documents(db, run)
    assert len(documents) == 1
    assert documents[0].content == text
    assert documents[0].source_url == fetch_boundaries.OVERPASS_URL


def test_failed_download_marks_the_run_failed(db, monkeypatch):
    def unreachable():
        raise OSError("server unreachable")

    monkeypatch.setattr(fetch_boundaries, "download", unreachable)

    run = fetch_boundaries.run_fetch(db)

    assert run.status == ScrapeStatus.FAILED
    assert "server unreachable" in run.error_message
    assert stored_documents(db, run) == []
