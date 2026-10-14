from sqlalchemy.dialects.postgresql import insert

from app.core.db import SessionLocal
from app.models import Department

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


def main():
    with SessionLocal() as db:
        seed_departments(db)


if __name__ == "__main__":
    main()
