from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.deps import assert_owner_or_admin, get_current_user, require_role
from app.core.config import settings
from app.core.db import get_db
from app.core.security import ALGORITHM, create_access_token, hash_password
from app.main import app
from app.models import Report, User
from app.models.enums import UserRole


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-for-auth-deps-0123456789")


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def gated(db):
    # small app of its own, so the role checks do not depend on real routes
    gated_app = FastAPI()

    @gated_app.get("/officer-only")
    def officer_only(user: Annotated[User, Depends(require_role(UserRole.OFFICER))]):
        return {"id": user.id}

    @gated_app.get("/staff")
    def staff(
        user: Annotated[User, Depends(require_role(UserRole.OFFICER, UserRole.ADMIN))],
    ):
        return {"id": user.id}

    @gated_app.get("/any-user")
    def any_user(user: Annotated[User, Depends(get_current_user)]):
        return {"id": user.id}

    gated_app.dependency_overrides[get_db] = lambda: db
    return TestClient(gated_app)


def add_user(db, email, role=UserRole.CITIZEN):
    user = User(
        name="Test User",
        email=email,
        password_hash=hash_password("longenough1"),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def token_for(user):
    return create_access_token(user)


def test_register_login_me_end_to_end(client):
    client.post(
        "/api/auth/register",
        json={"name": "Asha", "email": "asha@example.com", "password": "longenough1"},
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "asha@example.com", "password": "longenough1"},
    ).json()
    response = client.get("/api/auth/me", headers=bearer(login["access_token"]))

    assert response.status_code == 200
    assert response.json() == login["user"]


def test_me_without_a_token_is_401(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_role_comes_from_the_database_not_the_token(gated, db):
    user = add_user(db, "promoted@example.com", UserRole.CITIZEN)
    claims = {
        "sub": str(user.id),
        "role": "ADMIN",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    forged = jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)
    assert gated.get("/staff", headers=bearer(forged)).status_code == 403


def test_require_role_allows_a_matching_role(gated, db):
    officer = add_user(db, "officer@example.com", UserRole.OFFICER)
    response = gated.get("/officer-only", headers=bearer(token_for(officer)))
    assert response.status_code == 200
    assert response.json() == {"id": officer.id}


def test_require_role_rejects_other_roles_with_403(gated, db):
    citizen = add_user(db, "citizen@example.com", UserRole.CITIZEN)
    token = token_for(citizen)
    assert gated.get("/officer-only", headers=bearer(token)).status_code == 403
    assert gated.get("/staff", headers=bearer(token)).status_code == 403


def make_report(owner):
    return Report(user_id=owner.id)


def test_owner_can_access_their_report(db):
    owner = add_user(db, "owner@example.com")
    assert assert_owner_or_admin(owner, make_report(owner)) is None


def test_admin_can_access_any_report(db):
    owner = add_user(db, "owner@example.com")
    admin = add_user(db, "admin@example.com", UserRole.ADMIN)
    assert assert_owner_or_admin(admin, make_report(owner)) is None


def test_other_citizen_gets_404(db):
    owner = add_user(db, "owner@example.com")
    stranger = add_user(db, "stranger@example.com")
    with pytest.raises(HTTPException) as caught:
        assert_owner_or_admin(stranger, make_report(owner))
    assert caught.value.status_code == 404
