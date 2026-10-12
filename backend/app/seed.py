from sqlalchemy.dialects.postgresql import insert

from app.core.db import SessionLocal
from app.models import Department

DEPARTMENTS = [
    ("Roads and Infrastructure", "Potholes, damaged roads, footpaths and bridges"),
    ("Drainage and Sewerage", "Open manholes, blocked drains, sewage overflow"),
    ("Solid Waste Management", "Garbage collection and illegal dumping"),
    ("Street Lighting", "Broken or missing streetlights"),
    ("Water Supply", "Pipe leaks, no supply, contaminated water"),
    ("Electricity", "Power outages, exposed wires, damaged poles"),
    ("Parks and Public Spaces", "Parks, playgrounds and public property"),
    ("General", "Reports that do not fit any other department"),
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
