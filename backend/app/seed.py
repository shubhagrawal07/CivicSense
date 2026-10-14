from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.db import SessionLocal
from app.models import Authority, AuthorityContact, Department, GovernmentSource
from app.seed_data.mumbai import AUTHORITIES, SOURCES

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


def main():
    with SessionLocal() as db:
        seed_departments(db)
        seed_authorities(db)


if __name__ == "__main__":
    main()
