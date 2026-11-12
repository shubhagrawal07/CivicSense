import csv
import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func

from app.core.db import get_db
from app.main import app
from app.models import Authority, Department, Issue
from app.models.enums import IssueStatus, Severity

CATEGORY = "export-test-category"


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
    department_id=None,
    authority_id=None,
    is_synthetic=False,
):
    issue = Issue(
        category=category,
        severity=severity,
        status=status,
        location=func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
        report_count=1,
        last_reported_at=datetime(2026, 9, day, 12, tzinfo=timezone.utc),
        department_id=department_id,
        authority_id=authority_id,
        is_synthetic=is_synthetic,
    )
    db.add(issue)
    db.flush()
    return issue.id


def parse_csv(response):
    return list(csv.reader(io.StringIO(response.text)))


def test_header_row_and_row_count(client, db):
    add_issue(db)
    add_issue(db)

    response = client.get("/api/issues/export.csv", params={"category": CATEGORY})
    assert response.status_code == 200
    rows = parse_csv(response)

    assert rows[0] == [
        "id",
        "category",
        "severity",
        "status",
        "report_count",
        "department",
        "authority",
        "latitude",
        "longitude",
        "first_reported_at",
        "last_reported_at",
        "resolved_at",
        "is_synthetic",
    ]
    assert len(rows) - 1 == 2


def test_matches_map_api_for_the_same_filter(client, db):
    add_issue(db, lng=72.85, lat=19.05)
    add_issue(db, category="export-other-category")

    csv_response = client.get("/api/issues/export.csv", params={"category": CATEGORY})
    csv_ids = {int(row[0]) for row in parse_csv(csv_response)[1:]}

    map_response = client.get("/api/map/issues", params={"category": CATEGORY})
    map_ids = {
        feature["properties"]["id"] for feature in map_response.json()["features"]
    }

    assert csv_ids == map_ids


def test_content_type_and_disposition_headers(client, db):
    add_issue(db)

    response = client.get("/api/issues/export.csv", params={"category": CATEGORY})

    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == "attachment; filename=issues.csv"


def test_department_authority_and_synthetic_columns(client, db):
    dept = Department(name="export-test-dept")
    db.add(dept)
    db.flush()
    authority = Authority(
        name="export-test-authority", jurisdiction="test", department=dept
    )
    db.add(authority)
    db.flush()

    add_issue(
        db,
        department_id=dept.id,
        authority_id=authority.id,
        is_synthetic=True,
    )
    add_issue(db, is_synthetic=False)

    response = client.get("/api/issues/export.csv", params={"category": CATEGORY})
    rows = {row[0]: row for row in parse_csv(response)[1:]}

    synthetic_row = next(row for row in rows.values() if row[12] == "True")
    plain_row = next(row for row in rows.values() if row[12] == "False")

    assert synthetic_row[5] == "export-test-dept"
    assert synthetic_row[6] == "export-test-authority"
    assert plain_row[5] == ""
    assert plain_row[6] == ""
