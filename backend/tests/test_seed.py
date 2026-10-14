from sqlalchemy import func, select

from app.models import (
    Authority,
    AuthorityContact,
    Department,
    GovernmentSource,
    JurisdictionArea,
)
from app.models.enums import VerificationStatus
from app.seed import DEPARTMENTS, seed_authorities, seed_departments


def test_seed_can_run_repeatedly_without_duplicates(db):
    seed_departments(db)
    first = db.scalar(select(func.count()).select_from(Department))

    seed_departments(db)
    second = db.scalar(select(func.count()).select_from(Department))

    names = set(db.scalars(select(Department.name)))
    assert first == second
    assert {name for name, _ in DEPARTMENTS} <= names


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


def test_every_department_has_a_verified_contact_with_source(db):
    seed_departments(db)
    seed_authorities(db)

    for dept_id, name in db.execute(select(Department.id, Department.name)):
        verified = db.scalars(
            select(AuthorityContact)
            .join(Authority)
            .where(
                Authority.department_id == dept_id,
                AuthorityContact.verification_status == VerificationStatus.VERIFIED,
            )
        ).all()
        assert verified, name
        assert all(c.source_url and c.last_verified for c in verified), name
