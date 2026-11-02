from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Authority, AuthorityContact, Report, User
from app.models.enums import (
    ContactType,
    ProcessingStatus,
    UserRole,
    VerificationStatus,
)


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-for-quality-01234567")
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(db, email, role):
    user = User(
        name="Test", email=email, password_hash=hash_password("x" * 10), role=role
    )
    db.add(user)
    db.flush()
    return user


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def summary(client, user):
    response = client.get("/api/admin/data-quality", headers=auth(user))
    assert response.status_code == 200
    return response.json()


def test_counts_rows_with_missing_or_stale_data(client, db):
    admin = make_user(db, "quality-admin@example.com", UserRole.ADMIN)
    before = summary(client, admin)

    db.add(Report(user_id=admin.id, description=None, image_path=None))
    db.add(
        Report(
            user_id=admin.id,
            description="broken light",
            image_path="a.jpg",
            processing_status=ProcessingStatus.FAILED,
        )
    )
    authority = Authority(name="Test Ward Office", jurisdiction="test")
    db.add(authority)
    db.flush()
    old = date.today() - timedelta(days=200)
    db.add(
        AuthorityContact(
            authority_id=authority.id,
            type=ContactType.EMAIL,
            value="old@example.com",
            last_verified=old,
            verification_status=VerificationStatus.UNVERIFIED,
        )
    )
    db.add(
        AuthorityContact(
            authority_id=authority.id,
            type=ContactType.EMAIL,
            value="fresh@example.com",
            last_verified=date.today(),
            verification_status=VerificationStatus.VERIFIED,
        )
    )
    db.flush()

    after = summary(client, admin)
    assert (
        after["reports_without_description"] - before["reports_without_description"]
        == 1
    )
    assert after["reports_without_image"] - before["reports_without_image"] == 1
    assert after["reports_failed_processing"] - before["reports_failed_processing"] == 1
    assert after["contacts_unverified"] - before["contacts_unverified"] == 1
    assert (
        after["contacts_older_than_90_days"] - before["contacts_older_than_90_days"]
        == 1
    )


def test_only_admins_can_read_the_summary(client, db):
    citizen = make_user(db, "quality-citizen@example.com", UserRole.CITIZEN)

    assert client.get("/api/admin/data-quality").status_code == 401
    response = client.get("/api/admin/data-quality", headers=auth(citizen))
    assert response.status_code == 403
