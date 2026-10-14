import json

from sqlalchemy import select

from app.core.config import ROOT_DIR, settings
from app.models import Department

DEFAULT_DEPARTMENT = "General Grievance"


def _load_mapping():
    path = ROOT_DIR / "shared" / "category_departments.json"
    return json.loads(path.read_text(encoding="utf-8"))


CATEGORY_DEPARTMENTS = _load_mapping()


def department_for(db, category, confidence=1.0, threshold=None):
    if threshold is None:
        threshold = settings.text_confidence_threshold

    name = CATEGORY_DEPARTMENTS.get(category)
    if name is None:
        name, confidence = DEFAULT_DEPARTMENT, 0.0
    elif confidence < threshold:
        name = DEFAULT_DEPARTMENT

    row = db.scalar(select(Department).where(Department.name == name))
    if row is None:
        raise LookupError(f"department {name!r} is not in the database, run the seed")
    return {"department_id": row.id, "name": row.name, "confidence": confidence}
