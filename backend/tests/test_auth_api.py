import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_db
from app.core.security import decode_access_token
from app.main import app
from app.models import User
from app.models.enums import UserRole

NEW_USER = {"name": "Asha Rao", "email": "asha@example.com", "password": "longenough1"}


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-for-auth-api-0123456789")
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def register(client, **overrides):
    return client.post("/api/auth/register", json={**NEW_USER, **overrides})


def login(client, email=NEW_USER["email"], password=NEW_USER["password"]):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_register_returns_the_new_user(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "name", "email", "role"}
    assert body["name"] == "Asha Rao"
    assert body["email"] == "asha@example.com"
    assert body["role"] == "CITIZEN"


def test_register_never_returns_or_stores_the_plain_password(client, db):
    response = register(client)

    assert "password" not in response.text
    assert NEW_USER["password"] not in response.text
    stored = db.scalar(
        select(User.password_hash).where(User.email == NEW_USER["email"])
    )
    assert stored != NEW_USER["password"]
    assert stored.startswith("$argon2")


def test_register_ignores_a_role_sent_by_the_client(client, db):
    response = register(client, role="ADMIN")

    assert response.status_code == 201
    assert response.json()["role"] == "CITIZEN"
    role = db.scalar(select(User.role).where(User.email == NEW_USER["email"]))
    assert role == UserRole.CITIZEN


def test_duplicate_email_is_a_conflict(client):
    register(client)
    response = register(client, name="Someone Else")

    assert response.status_code == 409


def test_duplicate_email_ignores_case(client):
    register(client)
    response = register(client, email="ASHA@Example.com")

    assert response.status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"password": "short"},
        {"name": ""},
    ],
)
def test_register_rejects_invalid_input(client, overrides):
    assert register(client, **overrides).status_code == 422


def test_login_returns_a_token_and_the_user(client):
    created = register(client).json()
    response = login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"] == created
    claims = decode_access_token(body["access_token"])
    assert claims["sub"] == str(created["id"])
    assert claims["role"] == "CITIZEN"


def test_login_wrong_password_and_unknown_email_look_the_same(client):
    register(client)
    wrong_password = login(client, password="not the password")
    unknown_email = login(client, email="nobody@example.com")

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
