import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Issue, StatusHistory, User
from app.models.enums import IssueStatus, UserRole


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-for-admin-0123456789")
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


@pytest.fixture
def admin(db):
    return make_user(db, "admin@example.com", UserRole.ADMIN)


@pytest.fixture
def issue(db):
    issue = Issue(category="pothole")
    db.add(issue)
    db.flush()
    return issue


def patch(client, issue_id, user, **body):
    return client.patch(
        f"/api/admin/issues/{issue_id}/status",
        json=body,
        headers=auth(user) if user else {},
    )


def history(db, issue):
    return db.scalars(
        select(StatusHistory).where(StatusHistory.issue_id == issue.id)
    ).all()


def test_admin_changes_status_and_it_is_recorded(client, db, admin, issue):
    first = patch(client, issue.id, admin, status="IN_PROGRESS", note="crew sent")
    assert first.status_code == 200
    assert first.json()["id"] == issue.id
    assert first.json()["status"] == "IN_PROGRESS"
    assert first.json()["updated_at"]
    assert issue.resolved_at is None

    patch(client, issue.id, admin, status="RESOLVED")

    db.refresh(issue)
    assert issue.status == IssueStatus.RESOLVED
    assert issue.resolved_at is not None
    rows = history(db, issue)
    assert [(r.old_status, r.new_status) for r in rows] == [
        (IssueStatus.NEW, IssueStatus.IN_PROGRESS),
        (IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED),
    ]
    assert rows[0].note == "crew sent"
    assert rows[0].changed_by == admin.id


def test_unknown_status_is_400_and_unknown_issue_is_404(client, db, admin, issue):
    assert patch(client, issue.id, admin, status="DONE").status_code == 400
    assert patch(client, 999999, admin, status="CLOSED").status_code == 404

    db.refresh(issue)
    assert issue.status == IssueStatus.NEW
    assert history(db, issue) == []


def test_only_admins_can_change_status(client, db, issue):
    citizen = make_user(db, "citizen@example.com", UserRole.CITIZEN)

    assert patch(client, issue.id, None, status="CLOSED").status_code == 401
    assert patch(client, issue.id, citizen, status="CLOSED").status_code == 403

    db.refresh(issue)
    assert issue.status == IssueStatus.NEW
    assert history(db, issue) == []
