import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Department, Issue, IssueReport, Report, User
from app.models.enums import IssueStatus, ProcessingStatus, Severity, UserRole
from app.seed import seed_authorities, seed_departments

POINT = {"latitude": "19.1334", "longitude": "72.9133"}
TEXT = "Large pothole near the main gate, two scooters already slipped"


@pytest.fixture
def client(db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-for-reports-0123456789")
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(db, email, role=UserRole.CITIZEN):
    user = User(
        name="Test", email=email, password_hash=hash_password("x" * 10), role=role
    )
    db.add(user)
    db.flush()
    return user


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(user)}"}


@pytest.fixture
def citizen(db):
    return make_user(db, "citizen@example.com")


def picture(fmt="PNG", size=(200, 150)):
    buf = io.BytesIO()
    Image.new("RGB", size, "grey").save(buf, format=fmt)
    return buf.getvalue()


def submit(client, user, data=None, image=None, name="photo.png", ctype="image/png"):
    files = {"image": (name, image, ctype)} if image is not None else None
    return client.post(
        "/api/reports",
        data={**POINT, **(data or {})},
        files=files,
        headers=auth(user) if user else {},
    )


def test_description_only_is_accepted(client, db, citizen):
    response = submit(client, citizen, {"description": TEXT})

    assert response.status_code == 202
    body = response.json()
    assert set(body) == {"id", "processing_status", "created_at"}
    assert body["processing_status"] == "PENDING"
    report = db.get(Report, body["id"])
    assert report.user_id == citizen.id
    assert report.image_name is None
    assert report.description == TEXT


def test_image_only_is_accepted_and_stored(client, db, citizen):
    response = submit(client, citizen, image=picture())

    assert response.status_code == 202
    report = db.get(Report, response.json()["id"])
    assert report.description is None
    assert len(report.images) == 1
    assert report.images[0].position == 0
    assert report.image_name.endswith(".png")
    assert "photo" not in report.image_name
    assert (settings.upload_path / report.image_name).exists()


def test_jpeg_with_description_is_accepted(client, db, citizen):
    response = submit(
        client,
        citizen,
        {"description": TEXT},
        picture("JPEG"),
        name="a.jpeg",
        ctype="image/jpeg",
    )

    assert response.status_code == 202
    assert db.get(Report, response.json()["id"]).image_name.endswith(".jpg")


def test_stored_filenames_are_random(client, db, citizen):
    first = submit(client, citizen, image=picture())
    second = submit(client, citizen, image=picture())

    names = {db.get(Report, r.json()["id"]).image_name for r in (first, second)}
    assert len(names) == 2


def test_empty_file_part_counts_as_no_image(client, citizen):
    response = submit(client, citizen, {"description": TEXT}, b"", name="")

    assert response.status_code == 202


def test_no_token_is_401(client):
    response = submit(client, None, {"description": TEXT})

    assert response.status_code == 401


def test_neither_description_nor_image_is_422(client, citizen):
    response = submit(client, citizen)

    assert response.status_code == 422
    body = response.json()
    assert body["errors"][0]["field"] == "description"
    assert body["detail"]


def test_blank_description_without_image_is_422(client, citizen):
    assert submit(client, citizen, {"description": "   "}).status_code == 422


@pytest.mark.parametrize("text", ["too short", "x" * 1001])
def test_description_length_is_enforced(client, citizen, text):
    response = submit(client, citizen, {"description": text})

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "description"


def test_non_image_file_is_422(client, citizen):
    response = submit(client, citizen, image=b"%PDF-1.4 not a picture", name="a.png")

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "image"


def test_other_image_format_is_422(client, citizen):
    response = submit(
        client, citizen, image=picture("GIF"), name="a.gif", ctype="image/gif"
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "image"


def test_oversized_image_is_422(client, citizen, monkeypatch):
    monkeypatch.setattr(settings, "max_image_bytes", 1000)
    response = submit(client, citizen, image=picture(size=(600, 600)))

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "image"


@pytest.mark.parametrize("size", [(50, 50), (9000, 120)])
def test_image_dimensions_are_enforced(client, citizen, size):
    response = submit(client, citizen, image=picture(size=size))

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "image"


@pytest.mark.parametrize(
    "bad",
    [
        {"latitude": "91"},
        {"latitude": "-91"},
        {"longitude": "181"},
        {"latitude": "abc"},
    ],
)
def test_bad_coordinates_are_422(client, citizen, bad):
    response = submit(client, citizen, {"description": TEXT, **bad})

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] in {"latitude", "longitude"}


def test_missing_coordinates_are_422(client, citizen):
    response = client.post(
        "/api/reports", data={"description": TEXT}, headers=auth(citizen)
    )

    assert response.status_code == 422


def test_location_outside_configured_region_is_422(client, citizen, monkeypatch):
    monkeypatch.setattr(settings, "region_min_lat", 18.0)
    monkeypatch.setattr(settings, "region_max_lat", 20.0)
    monkeypatch.setattr(settings, "region_min_lng", 72.0)
    monkeypatch.setattr(settings, "region_max_lng", 73.5)

    inside = submit(client, citizen, {"description": TEXT})
    outside = submit(
        client, citizen, {"description": TEXT, "latitude": "28.6", "longitude": "77.2"}
    )

    assert inside.status_code == 202
    assert outside.status_code == 422


def test_rejected_upload_leaves_no_row(client, db, citizen):
    submit(client, citizen, image=b"junk")

    assert db.scalar(select(Report.id).where(Report.user_id == citizen.id)) is None


def test_get_pending_report_has_nulls(client, citizen):
    created = submit(client, citizen, {"description": TEXT}).json()

    response = client.get(f"/api/reports/{created['id']}", headers=auth(citizen))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["description"] == TEXT
    assert body["image_url"] is None
    assert body["location"] == {
        "lat": pytest.approx(19.1334),
        "lng": pytest.approx(72.9133),
    }
    assert body["processing_status"] == "PENDING"
    assert body["error"] is None
    for key in ("classification", "department", "severity", "issue", "authority"):
        assert body[key] is None


def test_get_report_returns_image_url(client, citizen):
    created = submit(client, citizen, image=picture()).json()

    body = client.get(f"/api/reports/{created['id']}", headers=auth(citizen)).json()

    assert body["image_url"].startswith("/uploads/")
    assert body["image_url"].endswith(".png")


def test_failed_report_shows_error_and_no_analysis(client, db, citizen):
    created = submit(client, citizen, {"description": TEXT}).json()
    report = db.get(Report, created["id"])
    report.processing_status = ProcessingStatus.FAILED
    report.error = "model unavailable"
    db.flush()

    body = client.get(f"/api/reports/{created['id']}", headers=auth(citizen)).json()

    assert body["processing_status"] == "FAILED"
    assert body["error"] == "model unavailable"
    assert body["classification"] is None


def test_done_report_carries_the_analysis(client, db, citizen):
    seed_departments(db)
    seed_authorities(db)
    created = submit(client, citizen, {"description": TEXT}).json()
    report = db.get(Report, created["id"])
    roads = db.scalar(
        select(Department).where(Department.name == "Roads / Public Works")
    )
    report.processing_status = ProcessingStatus.DONE
    report.classification = "pothole"
    report.classification_confidence = 0.9
    report.predicted_department_id = roads.id
    report.department_confidence = 0.8
    report.predicted_severity = Severity.HIGH
    db.flush()

    body = client.get(f"/api/reports/{created['id']}", headers=auth(citizen)).json()

    assert body["classification"]["category"] == "pothole"
    assert body["classification"]["needs_review"] is False
    assert body["department"] == {"id": roads.id, "name": roads.name, "confidence": 0.8}
    assert body["severity"]["level"] == "HIGH"
    assert body["issue"] is None
    assert body["authority"]["name"]
    assert isinstance(body["authority"]["contacts"], list)


def test_other_citizen_cannot_read_report(client, db, citizen):
    created = submit(client, citizen, {"description": TEXT}).json()
    other = make_user(db, "other@example.com")

    response = client.get(f"/api/reports/{created['id']}", headers=auth(other))

    assert response.status_code == 403
    assert TEXT not in response.text


def test_admin_can_read_any_report(client, db, citizen):
    created = submit(client, citizen, {"description": TEXT}).json()
    admin = make_user(db, "admin@example.com", UserRole.ADMIN)

    response = client.get(f"/api/reports/{created['id']}", headers=auth(admin))

    assert response.status_code == 200


def test_unknown_report_is_404(client, citizen):
    assert client.get("/api/reports/999999", headers=auth(citizen)).status_code == 404


def test_get_without_token_is_401(client):
    assert client.get("/api/reports/1").status_code == 401


def test_mine_lists_only_own_reports(client, db, citizen):
    other = make_user(db, "other@example.com")
    mine = submit(client, citizen, {"description": TEXT}).json()
    submit(client, other, {"description": TEXT})

    body = client.get("/api/reports/mine", headers=auth(citizen)).json()

    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [mine["id"]]


def test_mine_is_paginated_newest_first(client, db, citizen):
    ids = [
        submit(client, citizen, {"description": TEXT}).json()["id"] for _ in range(3)
    ]

    first = client.get("/api/reports/mine?limit=2", headers=auth(citizen)).json()
    second = client.get(
        "/api/reports/mine?limit=2&offset=2", headers=auth(citizen)
    ).json()

    assert first["total"] == 3
    assert [item["id"] for item in first["items"]] == [ids[2], ids[1]]
    assert [item["id"] for item in second["items"]] == [ids[0]]


def test_mine_hides_results_until_done(client, db, citizen):
    created = submit(client, citizen, {"description": TEXT}).json()

    pending = client.get("/api/reports/mine", headers=auth(citizen)).json()["items"][0]

    assert pending["processing_status"] == "PENDING"
    assert pending["description_preview"] == TEXT
    assert pending["thumbnail_url"] is None
    for key in (
        "category",
        "severity_level",
        "issue_id",
        "issue_status",
        "report_count",
    ):
        assert pending[key] is None

    report = db.get(Report, created["id"])
    report.processing_status = ProcessingStatus.DONE
    report.classification = "pothole"
    report.predicted_severity = Severity.HIGH
    issue = Issue(category="pothole", status=IssueStatus.NEW, report_count=2)
    db.add(issue)
    db.flush()
    db.add(IssueReport(issue_id=issue.id, report_id=report.id))
    db.flush()

    done = client.get("/api/reports/mine", headers=auth(citizen)).json()["items"][0]

    assert done["category"] == "pothole"
    assert done["severity_level"] == "HIGH"
    assert done["issue_id"] == issue.id
    assert done["issue_status"] == "NEW"
    assert done["report_count"] == 2
