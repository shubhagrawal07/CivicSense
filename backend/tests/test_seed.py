from sqlalchemy import func, select

from app.core.security import verify_password
from app.models import (
    Authority,
    AuthorityContact,
    GovernmentSource,
    JurisdictionArea,
    User,
)
from app.models.enums import UserRole
from app.seed import seed_admin, seed_authorities, seed_departments


def test_authority_seed_is_repeatable(db):
    def counts():
        return [
            db.scalar(select(func.count()).select_from(model))
            for model in (
                Authority,
                AuthorityContact,
                GovernmentSource,
                JurisdictionArea,
            )
        ]

    seed_departments(db)
    seed_authorities(db)
    first = counts()
    seed_authorities(db)
    assert counts() == first


def test_admin_seed_creates_one_admin_who_can_log_in(db):
    assert seed_admin(db, "Demo Admin", "Admin@Example.com", "demo-password-1")
    user = db.scalar(select(User).where(User.email == "admin@example.com"))

    assert user.role == UserRole.ADMIN
    assert user.name == "Demo Admin"
    assert user.password_hash != "demo-password-1"
    assert verify_password("demo-password-1", user.password_hash)


def test_admin_seed_is_repeatable_and_keeps_the_existing_user(db):
    seed_admin(db, "Demo Admin", "admin@example.com", "demo-password-1")
    again = seed_admin(db, "Other Name", "admin@example.com", "different-password")
    count = db.scalar(
        select(func.count()).select_from(User).where(User.email == "admin@example.com")
    )
    name = db.scalar(select(User.name).where(User.email == "admin@example.com"))

    assert again is False
    assert count == 1
    assert name == "Demo Admin"
