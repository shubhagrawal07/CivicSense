import io
import os
import time
import uuid

import httpx
import pytest
from PIL import Image
from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.demo_seed import remove_users
from app.models import User
from app.models.enums import IssueStatus
from app.seed import seed_admin, seed_authorities, seed_departments
from app.services.reports import create_report
from app.workers import pipeline
from app.workers.pipeline import process_report

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000")
POLL_TIMEOUT = float(os.environ.get("E2E_TIMEOUT", "30"))
PASSWORD = "e2e-password-1"

GATE = (19.1334, 72.9133)
NEAR_GATE = (19.13345, 72.91336)
FAR_AWAY = (19.1362, 72.9118)

POTHOLE = "Big pothole near the main gate, two scooters have already slipped on it"
POTHOLE_AGAIN = (
    "Deep pothole at the main gate road, a scooter slipped here this morning"
)


@pytest.fixture(scope="module")
def api():
    client = httpx.Client(base_url=BASE_URL, timeout=15)
    try:
        client.get("/api/health").raise_for_status()
    except httpx.HTTPError:
        pytest.skip(f"backend is not running at {BASE_URL}")
    yield client
    client.close()


@pytest.fixture(scope="module")
def run_id():
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="module", autouse=True)
def cleanup(api, run_id):
    with SessionLocal() as db:
        seed_departments(db)
        seed_authorities(db)
    yield
    with SessionLocal() as db:
        ids = db.scalars(
            select(User.id).where(User.email.like(f"e2e.%.{run_id}@example.com"))
        ).all()
        remove_users(db, ids)


def sign_in(api, email):
    response = api.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="module")
def citizen(api, run_id):
    email = f"e2e.citizen.{run_id}@example.com"
    body = {"name": "E2E Citizen", "email": email, "password": PASSWORD}
    response = api.post("/api/auth/register", json=body)
    assert response.status_code == 201
    assert response.json()["role"] == "CITIZEN"
    return {"id": response.json()["id"], "headers": sign_in(api, email)}


@pytest.fixture(scope="module")
def admin(api, run_id):
    email = f"e2e.admin.{run_id}@example.com"
    with SessionLocal() as db:
        assert seed_admin(db, "E2E Admin", email, PASSWORD)
    return sign_in(api, email)


def png(size=(320, 240)):
    buf = io.BytesIO()
    Image.new("RGB", size, "grey").save(buf, format="PNG")
    return buf.getvalue()


def submit(api, headers, text, where, photo=None):
    data = {"latitude": str(where[0]), "longitude": str(where[1])}
    if text is not None:
        data["description"] = text
    files = {"image": ("evidence.png", photo, "image/png")} if photo else None
    return api.post("/api/reports", data=data, files=files, headers=headers)


def wait_until_finished(api, headers, report_id):
    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        body = api.get(f"/api/reports/{report_id}", headers=headers).json()
        if body["processing_status"] in ("DONE", "FAILED"):
            return body
        time.sleep(0.5)
    pytest.fail(f"report {report_id} did not finish within {POLL_TIMEOUT} seconds")


def test_full_flow(api, citizen, admin):
    headers = citizen["headers"]

    first = submit(api, headers, POTHOLE, GATE)
    assert first.status_code == 202
    assert first.json()["processing_status"] == "PENDING"
    first_id = first.json()["id"]

    result = wait_until_finished(api, headers, first_id)
    assert result["processing_status"] == "DONE"
    assert result["error"] is None
    assert result["description"] == POTHOLE
    assert result["image_url"] is None
    assert result["location"] == pytest.approx({"lat": GATE[0], "lng": GATE[1]})
    assert result["classification"]["category"] == "pothole"
    assert result["classification"]["confidence"] >= settings.text_confidence_threshold
    assert result["classification"]["needs_review"] is False
    assert result["department"]["name"] == "Roads / Public Works"
    assert result["severity"]["level"] == "LOW"
    assert result["issue"]["is_new"] is True
    assert result["issue"]["report_count"] == 1
    assert result["authority"]["name"]
    assert result["authority"]["contacts"]
    issue_id = result["issue"]["id"]

    second = submit(api, headers, POTHOLE_AGAIN, NEAR_GATE)
    assert second.status_code == 202
    second_id = second.json()["id"]
    linked = wait_until_finished(api, headers, second_id)
    assert linked["processing_status"] == "DONE"
    assert linked["issue"]["id"] == issue_id
    assert linked["issue"]["is_new"] is False
    assert linked["issue"]["report_count"] == 2

    mine = api.get("/api/reports/mine", headers=headers).json()
    assert mine["total"] == 2
    assert [item["id"] for item in mine["items"]] == [second_id, first_id]
    assert {item["processing_status"] for item in mine["items"]} == {"DONE"}
    assert {item["issue_id"] for item in mine["items"]} == {issue_id}

    change = api.patch(
        f"/api/admin/issues/{issue_id}/status",
        json={"status": "ASSIGNED", "note": "Sent to the campus maintenance team"},
        headers=admin,
    )
    assert change.status_code == 200
    issue = api.get(f"/api/issues/{issue_id}").json()
    assert issue["status"] == "ASSIGNED"
    assert issue["report_count"] == 2
    history = [(row["status"], row["note"]) for row in issue["status_history"]]
    assert history[0][0] == IssueStatus.NEW
    assert history[-1] == ("ASSIGNED", "Sent to the campus maintenance team")


def test_citizen_cannot_change_status(api, citizen):
    response = api.patch(
        "/api/admin/issues/1/status",
        json={"status": "CLOSED"},
        headers=citizen["headers"],
    )

    assert response.status_code == 403


def test_photo_is_kept_but_does_not_change_the_category(api, citizen):
    headers = citizen["headers"]
    plain = wait_until_finished(
        api, headers, submit(api, headers, POTHOLE, FAR_AWAY).json()["id"]
    )
    far = (FAR_AWAY[0] + 0.01, FAR_AWAY[1])
    with_photo = wait_until_finished(
        api, headers, submit(api, headers, POTHOLE, far, png()).json()["id"]
    )

    assert with_photo["processing_status"] == "DONE"
    assert with_photo["image_url"].startswith("/uploads/")
    assert api.get(with_photo["image_url"]).headers["content-type"] == "image/png"
    assert with_photo["classification"] == plain["classification"]
    assert with_photo["department"] == plain["department"]


def test_missing_description_is_rejected(api, citizen):
    headers = citizen["headers"]

    for photo in (None, png()):
        response = submit(api, headers, None, GATE, photo)
        assert response.status_code == 422
        assert response.json()["errors"][0]["field"] == "description"

    assert submit(api, headers, "   ", GATE).status_code == 422
    assert submit(api, headers, "too short", GATE).status_code == 422


def test_failing_stage_marks_the_report_failed(api, citizen, monkeypatch):
    def broken(db, report):
        raise RuntimeError("severity stage is down")

    monkeypatch.setattr(pipeline, "stage_severity", broken)
    with SessionLocal() as db:
        report = create_report(db, citizen["id"], POTHOLE, None, *FAR_AWAY)
        report_id = report.id
    process_report(report_id)

    body = api.get(f"/api/reports/{report_id}", headers=citizen["headers"]).json()
    assert body["processing_status"] == "FAILED"
    assert "severity stage is down" in body["error"]
    assert body["issue"] is None
    mine = api.get("/api/reports/mine", headers=citizen["headers"]).json()
    failed = [item for item in mine["items"] if item["id"] == report_id]
    assert failed[0]["processing_status"] == "FAILED"


def test_other_citizen_cannot_read_a_report(api, citizen, run_id):
    email = f"e2e.other.{run_id}@example.com"
    body = {"name": "Other", "email": email, "password": PASSWORD}
    assert api.post("/api/auth/register", json=body).status_code == 201
    created = submit(api, citizen["headers"], POTHOLE, GATE).json()

    response = api.get(f"/api/reports/{created['id']}", headers=sign_in(api, email))

    assert response.status_code == 403
