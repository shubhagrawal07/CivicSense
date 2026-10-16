import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import get_db
from app.main import app
from app.models import Department
from app.seed import seed_authorities, seed_departments

MAIN_BUILDING = {"lat": 19.1334, "lng": 72.9133}
HIRANANDANI = {"lat": 19.1176, "lng": 72.9060}


@pytest.fixture
def client(db):
    seed_departments(db)
    seed_authorities(db)
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def dept_id(db, name):
    return db.scalar(select(Department.id).where(Department.name == name))


def get(client, db, dept_name, point, **extra):
    params = {"department_id": dept_id(db, dept_name), **point, **extra}
    return client.get("/api/authority-info", params=params)


def test_response_has_the_documented_shape(client, db):
    response = get(client, db, "Roads / Public Works", MAIN_BUILDING)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "department",
        "authority",
        "contacts",
        "is_fallback",
        "needs_review",
        "other_matches",
    }
    assert body["department"]["name"] == "Roads / Public Works"
    assert set(body["authority"]) == {"id", "name", "jurisdiction"}
    assert set(body["contacts"][0]) == {
        "type",
        "value",
        "source_url",
        "last_verified_at",
        "verified",
    }


def test_road_issue_on_campus_returns_iitb_with_its_portal(client, db):
    body = get(client, db, "Roads / Public Works", MAIN_BUILDING).json()

    assert body["authority"]["name"] == "IIT Bombay Civil Maintenance"
    assert body["is_fallback"] is False
    assert body["needs_review"] is False
    portal = [c for c in body["contacts"] if c["type"] == "COMPLAINT_PORTAL"]
    assert portal[0]["value"].startswith("https://support.iitb.ac.in")
    assert portal[0]["verified"] is True
    assert portal[0]["last_verified_at"]


def test_unknown_department_is_404(client):
    response = client.get(
        "/api/authority-info", params={"department_id": 999999, **MAIN_BUILDING}
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"lat": 19.1, "lng": 72.9},
        {"department_id": 1, "lat": "north", "lng": 72.9},
        {"department_id": 1, "lat": 91, "lng": 72.9},
    ],
)
def test_missing_or_invalid_parameters_are_422(client, params):
    assert client.get("/api/authority-info", params=params).status_code == 422
