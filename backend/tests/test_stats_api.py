from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app
from app.models import Issue
from app.models.enums import IssueStatus, Severity


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
