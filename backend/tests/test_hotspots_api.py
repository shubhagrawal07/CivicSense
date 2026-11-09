from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func

from app.core.db import get_db
from app.main import app
from app.models import Issue
from app.models.enums import IssueStatus, Severity

CATEGORY = "hotspot-test-category"


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def add_issue(
    db,
    category=CATEGORY,
    severity=Severity.MEDIUM,
    age_days=5,
    lng=72.9,
    lat=19.1,
):
    now = datetime.now(timezone.utc)
    issue = Issue(
        category=category,
        severity=severity,
        status=IssueStatus.NEW,
        location=func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
        report_count=1,
        last_reported_at=now - timedelta(days=age_days),
    )
    db.add(issue)
    db.flush()
    return issue.id


def test_known_answer_for_a_small_hand_built_set(client, db):
    add_issue(db, severity=Severity.CRITICAL, age_days=5, lng=72.9, lat=19.1)
    add_issue(db, severity=Severity.LOW, age_days=10, lng=72.9001, lat=19.1001)
    add_issue(db, severity=Severity.HIGH, age_days=40, lng=73.0, lat=19.2)

    response = client.get("/api/hotspots", params={"category": CATEGORY})
    assert response.status_code == 200
    cells = response.json()

    assert len(cells) == 2
    assert cells[0]["lat"] == pytest.approx(19.1)
    assert cells[0]["lng"] == pytest.approx(72.9)
    assert cells[0]["count"] == 2
    assert cells[0]["score"] == pytest.approx(5.0)

    assert cells[1]["lat"] == pytest.approx(19.2)
    assert cells[1]["lng"] == pytest.approx(73.0)
    assert cells[1]["count"] == 1
    assert cells[1]["score"] == pytest.approx(1.5)


def test_category_filters_result(client, db):
    add_issue(db, category=CATEGORY, lng=72.9, lat=19.1)
    add_issue(db, category="other-category", lng=72.95, lat=19.15)

    response = client.get("/api/hotspots", params={"category": CATEGORY})
    cells = response.json()

    assert len(cells) == 1
    assert cells[0]["lat"] == pytest.approx(19.1)


def test_days_filters_result(client, db):
    add_issue(db, category=CATEGORY, age_days=5, lng=72.9, lat=19.1)
    add_issue(db, category=CATEGORY, age_days=200, lng=73.0, lat=19.2)

    short_window = client.get(
        "/api/hotspots", params={"category": CATEGORY, "days": 90}
    ).json()
    assert len(short_window) == 1

    long_window = client.get(
        "/api/hotspots", params={"category": CATEGORY, "days": 250}
    ).json()
    assert len(long_window) == 2


def test_limit_truncates_result(client, db):
    add_issue(db, category=CATEGORY, severity=Severity.CRITICAL, lng=72.9, lat=19.1)
    add_issue(db, category=CATEGORY, severity=Severity.LOW, lng=73.0, lat=19.2)

    response = client.get("/api/hotspots", params={"category": CATEGORY, "limit": 1})
    cells = response.json()

    assert len(cells) == 1
    assert cells[0]["lat"] == pytest.approx(19.1)
