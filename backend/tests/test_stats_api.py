from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
from shapely.geometry import MultiPolygon, box
from sqlalchemy import func

from app.core.db import get_db
from app.main import app
from app.models import Issue, Jurisdiction
from app.models.enums import IssueStatus, JurisdictionStatus, Severity


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def add_issue(db, status, days_to_resolve=None):
    reported = datetime(2026, 9, 1, tzinfo=timezone.utc)
    resolved = None
    if days_to_resolve is not None:
        resolved = reported + timedelta(days=days_to_resolve)
    db.add(
        Issue(
            category="pothole",
            status=status,
            first_reported_at=reported,
            resolved_at=resolved,
        )
    )
    db.flush()


def summary(client):
    response = client.get("/api/stats/summary")
    assert response.status_code == 200
    return response.json()


def test_counts_each_bucket_and_total(client, db):
    before = summary(client)

    add_issue(db, IssueStatus.NEW)
    add_issue(db, IssueStatus.ASSIGNED)
    add_issue(db, IssueStatus.REOPENED)
    add_issue(db, IssueStatus.IN_PROGRESS)
    add_issue(db, IssueStatus.RESOLVED, days_to_resolve=2)
    add_issue(db, IssueStatus.CLOSED, days_to_resolve=3)
    add_issue(db, IssueStatus.DUPLICATE)

    after = summary(client)
    assert after["total"] - before["total"] == 7
    assert after["open"] - before["open"] == 3
    assert after["in_progress"] - before["in_progress"] == 1
    assert after["resolved"] - before["resolved"] == 2


def test_average_resolution_time_is_in_days(client, db):
    if summary(client)["resolved"]:
        pytest.skip("database already holds resolved issues")

    add_issue(db, IssueStatus.RESOLVED, days_to_resolve=2)
    add_issue(db, IssueStatus.VERIFIED, days_to_resolve=3)
    # resolved but never stamped, so it must not drag the average down
    add_issue(db, IssueStatus.RESOLVED)

    assert summary(client)["avg_resolution_days"] == 2.5


def test_average_is_null_without_resolved_issues(client, db):
    if summary(client)["resolved"]:
        pytest.skip("database already holds resolved issues")

    add_issue(db, IssueStatus.NEW)

    body = summary(client)
    assert body["avg_resolution_days"] is None
    assert set(body) == {
        "total",
        "open",
        "in_progress",
        "resolved",
        "avg_resolution_days",
    }


def add_classified(db, category, severity, status=IssueStatus.NEW):
    db.add(Issue(category=category, severity=severity, status=status))
    db.flush()


def test_breakdown_groups_and_sorts_by_count(client, db):
    if summary(client)["total"]:
        pytest.skip("database already holds issues")

    add_classified(db, "pothole", Severity.HIGH)
    add_classified(db, "pothole", Severity.HIGH)
    add_classified(db, "pothole", Severity.LOW, IssueStatus.RESOLVED)
    add_classified(db, "garbage", Severity.CRITICAL, IssueStatus.IN_PROGRESS)
    add_classified(db, "streetlight", None)

    body = client.get("/api/stats/breakdown").json()
    assert body["by_category"] == [
        {"category": "pothole", "count": 3},
        {"category": "garbage", "count": 1},
        {"category": "streetlight", "count": 1},
    ]
    assert body["by_severity"] == [
        {"severity": "HIGH", "count": 2},
        {"severity": "LOW", "count": 1},
        {"severity": "CRITICAL", "count": 1},
    ]
    total = sum(row["count"] for row in body["by_category"])
    assert total == summary(client)["total"]


def test_breakdown_status_filter(client, db):
    if summary(client)["total"]:
        pytest.skip("database already holds issues")

    add_classified(db, "pothole", Severity.HIGH)
    add_classified(db, "pothole", Severity.LOW, IssueStatus.CLOSED)
    add_classified(db, "garbage", Severity.LOW, IssueStatus.IN_PROGRESS)

    resolved = client.get("/api/stats/breakdown", params={"status": "resolved"})
    assert resolved.json()["by_category"] == [{"category": "pothole", "count": 1}]

    active = client.get("/api/stats/breakdown", params={"status": "in_progress"})
    assert active.json()["by_category"] == [{"category": "garbage", "count": 1}]

    bad = client.get("/api/stats/breakdown", params={"status": "bogus"})
    assert bad.status_code == 422


def add_reported(db, category, when):
    db.add(Issue(category=category, status=IssueStatus.NEW, first_reported_at=when))
    db.flush()


def trend(client, **params):
    response = client.get("/api/stats/trend", params=params)
    assert response.status_code == 200
    return response.json()


def test_trend_by_day(client, db):
    utc = timezone.utc
    add_reported(db, "trend_day", datetime(2026, 9, 7, 3, tzinfo=utc))
    add_reported(db, "trend_day", datetime(2026, 9, 7, 22, tzinfo=utc))
    add_reported(db, "trend_day", datetime(2026, 9, 9, 1, tzinfo=utc))
    add_reported(db, "trend_other", datetime(2026, 9, 7, 5, tzinfo=utc))

    body = trend(client, interval="day", category="trend_day")
    assert body == [
        {"period": "2026-09-07", "count": 2},
        {"period": "2026-09-09", "count": 1},
    ]

    window = trend(
        client,
        interval="day",
        category="trend_day",
        **{"from": "2026-09-08", "to": "2026-09-09"},
    )
    assert window == [{"period": "2026-09-09", "count": 1}]


def test_trend_by_week_is_default_and_labelled_by_monday(client, db):
    utc = timezone.utc
    # 2026-09-07 is a Monday, 2026-09-13 the Sunday that closes that week
    add_reported(db, "trend_week", datetime(2026, 9, 7, 0, 30, tzinfo=utc))
    add_reported(db, "trend_week", datetime(2026, 9, 13, 23, 30, tzinfo=utc))
    add_reported(db, "trend_week", datetime(2026, 9, 14, 0, 30, tzinfo=utc))

    expected = [
        {"period": "2026-09-07", "count": 2},
        {"period": "2026-09-14", "count": 1},
    ]
    assert trend(client, category="trend_week") == expected
    assert trend(client, interval="week", category="trend_week") == expected


def test_trend_rejects_bad_parameters(client):
    bad_interval = client.get("/api/stats/trend", params={"interval": "month"})
    assert bad_interval.status_code == 422
    backwards = {"from": "2026-10-01", "to": "2026-09-01"}
    assert client.get("/api/stats/trend", params=backwards).status_code == 422


def add_ward(db, name, west, south):
    shape = MultiPolygon([box(west, south, west + 1, south + 1)])
    ward = Jurisdiction(
        name=name,
        type="ward",
        boundary=from_shape(shape, srid=4326),
        status=JurisdictionStatus.APPROVED,
    )
    db.add(ward)
    db.flush()
    return ward


def add_issue_at(db, lng, lat, category, status, severity):
    db.add(
        Issue(
            category=category,
            status=status,
            severity=severity,
            first_reported_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            location=func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
        )
    )
    db.flush()


def test_by_ward_counts_issues_in_each_ward(client, db):
    ward_a = add_ward(db, "Test Ward A", 10, 10)
    ward_b = add_ward(db, "Test Ward B", 20, 20)
    ward_c = add_ward(db, "Test Ward C", 30, 30)
    add_issue_at(db, 10.5, 10.5, "pothole", IssueStatus.NEW, Severity.HIGH)
    add_issue_at(db, 10.6, 10.6, "pothole", IssueStatus.RESOLVED, Severity.LOW)
    add_issue_at(db, 10.7, 10.7, "garbage", IssueStatus.NEW, Severity.CRITICAL)
    add_issue_at(db, 20.5, 20.5, "pothole", IssueStatus.IN_PROGRESS, Severity.MEDIUM)
    add_issue_at(db, 50.5, 50.5, "pothole", IssueStatus.NEW, Severity.HIGH)

    def counts(params=None):
        response = client.get("/api/stats/by-ward", params=params)
        assert response.status_code == 200
        rows = {row["ward_id"]: row for row in response.json()}
        return [
            (
                rows[ward.id]["issue_count"],
                rows[ward.id]["open_count"],
                rows[ward.id]["high_severity_count"],
            )
            for ward in (ward_a, ward_b, ward_c)
        ]

    assert counts() == [(3, 2, 2), (1, 0, 0), (0, 0, 0)]
    assert counts({"category": "garbage"}) == [(1, 1, 1), (0, 0, 0), (0, 0, 0)]
