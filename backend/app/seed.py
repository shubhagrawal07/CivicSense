import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import (
    Authority,
    AuthorityContact,
    Department,
    GovernmentSource,
    JurisdictionArea,
    User,
)
from app.models.enums import UserRole
from app.schemas.auth import MIN_PASSWORD_LENGTH
from app.seed_data.mumbai import AREAS, AUTHORITIES, SOURCES
from app.services.auth import normalize_email

SEED_DATA = Path(__file__).parent / "seed_data"

DEPARTMENTS = [
    ("Roads / Public Works", "Potholes, road obstructions, damaged infrastructure"),
    ("Drainage / Sewerage", "Drainage and sewage problems, open manholes"),
    ("Water Supply", "Water leakage"),
    ("Sanitation / Solid Waste", "Garbage"),
    ("Electricity", "Power outages, streetlights"),
    ("General Grievance", "Reports that do not fit any other department"),
]


def seed_departments(db):
    stmt = insert(Department).values(
        [{"name": n, "description": d} for n, d in DEPARTMENTS]
    )
    db.execute(stmt.on_conflict_do_nothing(index_elements=["name"]))
    db.commit()


def seed_areas(db):
    for authority_name, label, filename, priority, source_url, status in AREAS:
        authority_id = db.scalar(
            select(Authority.id).where(Authority.name == authority_name)
        )
        found = db.scalar(
            select(JurisdictionArea.id).where(
                JurisdictionArea.authority_id == authority_id,
                JurisdictionArea.label == label,
            )
        )
        if found is not None:
            continue
        collection = json.loads((SEED_DATA / filename).read_text())
        geometry = json.dumps(collection["features"][0]["geometry"])
        shape = func.ST_Multi(func.ST_SetSRID(func.ST_GeomFromGeoJSON(geometry), 4326))
        db.add(
            JurisdictionArea(
                authority_id=authority_id,
                label=label,
                area=shape,
                priority=priority,
                source_url=source_url,
                verification_status=status,
            )
        )


def seed_authorities(db):
    dept_ids = dict(db.execute(select(Department.name, Department.id)).all())
    for dept_name, authorities in AUTHORITIES.items():
        for name, jurisdiction, contacts in authorities:
            authority = db.scalar(
                select(Authority).where(
                    Authority.name == name,
                    Authority.department_id == dept_ids[dept_name],
                )
            )
            if authority is None:
                authority = Authority(
                    name=name,
                    jurisdiction=jurisdiction,
                    department_id=dept_ids[dept_name],
                )
                db.add(authority)
                db.flush()
            for kind, value, source_url, verified_on, status in contacts:
                exists = db.scalar(
                    select(AuthorityContact.id).where(
                        AuthorityContact.authority_id == authority.id,
                        AuthorityContact.type == kind,
                        AuthorityContact.value == value,
                    )
                )
                if exists is None:
                    db.add(
                        AuthorityContact(
                            authority_id=authority.id,
                            type=kind,
                            value=value,
                            source_url=source_url,
                            last_verified=verified_on,
                            verification_status=status,
                        )
                    )
    db.flush()
    seed_areas(db)
    for domain, url, dept_name, authority_name in SOURCES:
        if db.scalar(
            select(GovernmentSource.id).where(GovernmentSource.source_url == url)
        ):
            continue
        authority_id = db.scalar(
            select(Authority.id).where(Authority.name == authority_name)
        )
        db.add(
            GovernmentSource(
                domain=domain,
                source_url=url,
                department_id=dept_ids.get(dept_name),
                authority_id=authority_id,
                jurisdiction="Mumbai",
            )
        )
    db.commit()


def seed_admin(db, name, email, password):
    email = normalize_email(email)
    if db.scalar(select(User.id).where(User.email == email)):
        return False
    db.add(
        User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
    )
    db.commit()
    return True


def main():
    with SessionLocal() as db:
        seed_departments(db)
        seed_authorities(db)

        if not (settings.admin_email and settings.admin_password):
            print("ADMIN_EMAIL or ADMIN_PASSWORD not set, skipping the admin user")
        elif len(settings.admin_password) < MIN_PASSWORD_LENGTH:
            raise SystemExit(
                f"ADMIN_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters"
            )
        elif seed_admin(
            db, settings.admin_name, settings.admin_email, settings.admin_password
        ):
            print(f"created admin {normalize_email(settings.admin_email)}")
        else:
            print("admin already exists, left unchanged")


if __name__ == "__main__":
    main()
