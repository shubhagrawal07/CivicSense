# AI-generated test code
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import get_db
from app.core.security import hash_password
from app.main import app
from app.models import IssueReport, User
from app.seed import seed_authorities, seed_departments
from app.services.reports import create_report
from app.workers import pipeline

LAT, LNG = 19.1334, 72.9133
TEXT = "Large pothole near the main gate, two scooters already slipped"


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def processed_issue_id(db, monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "classify_text",
        lambda text: {
            "category": "pothole",
            "confidence": 0.9,
            "top_k": [],
            "needs_review": False,
        },
    )
    seed_departments(db)
    seed_authorities(db)
    user = User(
        name="T", email="issue@example.com", password_hash=hash_password("x" * 10)
    )
    db.add(user)
    db.flush()
    report = create_report(db, user.id, TEXT, None, LAT, LNG)

    pipeline.process_report(report.id, db)

    link = db.scalar(select(IssueReport).where(IssueReport.report_id == report.id))
    return link.issue_id


def test_issue_detail_has_everything_the_page_needs(client, processed_issue_id):
    response = client.get(f"/api/issues/{processed_issue_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == processed_issue_id
    assert body["category"] == "pothole"
    assert body["status"] == "NEW"
    assert body["severity"] is not None
    assert body["report_count"] == 1
    assert body["location"] == pytest.approx({"lat": LAT, "lng": LNG})
    assert body["first_reported_at"] and body["last_reported_at"]
    assert body["department"]["name"] == "Roads / Public Works"
    assert body["authority"]["name"]
    assert isinstance(body["contacts"], list)
    assert [h["status"] for h in body["status_history"]] == ["NEW"]
    assert body["status_history"][0]["note"]


def test_unknown_issue_is_404(client):
    response = client.get("/api/issues/999999")

    assert response.status_code == 404
