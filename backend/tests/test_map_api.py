from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func

from app.core.db import get_db
from app.main import app
from app.models import Issue
from app.models.enums import IssueStatus, Severity

CATEGORY = "map-test-category"


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def add_issue(
    db,
    category=CATEGORY,
    severity=Severity.MEDIUM,
    status=IssueStatus.NEW,
    day=1,
    lng=72.9,
    lat=19.1,
):
    issue = Issue(
        category=category,
        severity=severity,
        status=status,
        location=func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
        report_count=1,
        last_reported_at=datetime(2026, 9, day, 12, tzinfo=timezone.utc),
    )
    db.add(issue)
    db.flush()
    return issue.id


def ids(client, **params):
    params.setdefault("category", CATEGORY)
    response = client.get("/api/map/issues", params=params)
    assert response.status_code == 200
    return {feature["properties"]["id"] for feature in response.json()["features"]}


def test_returns_geojson_filtered_by_category(client, db):
    issue_id = add_issue(db, lng=72.85, lat=19.05)
    add_issue(db, category="map-test-other")

    response = client.get("/api/map/issues", params={"category": CATEGORY})
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    feature = body["features"][0]
    assert feature["geometry"] == {"type": "Point", "coordinates": [72.85, 19.05]}
    assert feature["properties"]["id"] == issue_id


def test_filters_by_severity_and_status(client, db):
    high = add_issue(db, severity=Severity.HIGH)
    critical = add_issue(db, severity=Severity.CRITICAL, status=IssueStatus.CLOSED)
    add_issue(db, severity=Severity.LOW)

    assert ids(client, severity=["HIGH", "CRITICAL"]) == {high, critical}
    assert ids(client, severity="CRITICAL", status="resolved") == {critical}


def test_filters_by_date_range(client, db):
    add_issue(db, day=1)
    middle = add_issue(db, day=10)
    add_issue(db, day=20)

    assert ids(client, **{"from": "2026-09-05", "to": "2026-09-10"}) == {middle}
