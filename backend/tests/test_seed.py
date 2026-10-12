from sqlalchemy import func, select

from app.models import Department
from app.seed import DEPARTMENTS, seed_departments


def test_seed_can_run_repeatedly_without_duplicates(db):
    seed_departments(db)
    first = db.scalar(select(func.count()).select_from(Department))

    seed_departments(db)
    second = db.scalar(select(func.count()).select_from(Department))

    names = set(db.scalars(select(Department.name)))
    assert first == second
    assert {name for name, _ in DEPARTMENTS} <= names
