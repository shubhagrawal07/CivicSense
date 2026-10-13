import json

import pytest

from app.core.config import ROOT_DIR
from app.intelligence.departments import (
    CATEGORY_DEPARTMENTS,
    DEFAULT_DEPARTMENT,
    department_for,
)
from app.seed import DEPARTMENTS, seed_departments

taxonomy = json.loads((ROOT_DIR / "shared" / "categories.json").read_text())
category_keys = [c["key"] for c in taxonomy["categories"]]


def test_every_category_has_exactly_one_department():
    assert set(CATEGORY_DEPARTMENTS) == set(category_keys)
    assert all(isinstance(v, str) for v in CATEGORY_DEPARTMENTS.values())


def test_mapped_departments_are_seeded():
    seeded = {name for name, _ in DEPARTMENTS}
    assert set(CATEGORY_DEPARTMENTS.values()) <= seeded
    assert DEFAULT_DEPARTMENT in seeded


def test_fallback_category_goes_to_default_department():
    assert CATEGORY_DEPARTMENTS[taxonomy["fallback"]] == DEFAULT_DEPARTMENT


@pytest.mark.parametrize("category", category_keys)
def test_department_for_every_category(db, category):
    seed_departments(db)
    result = department_for(db, category, confidence=0.9)
    assert result["name"] == CATEGORY_DEPARTMENTS[category]
    assert result["confidence"] == 0.9
    assert isinstance(result["department_id"], int)


def test_unknown_category_uses_default(db):
    seed_departments(db)
    result = department_for(db, "not_a_category", confidence=0.95)
    assert result["name"] == DEFAULT_DEPARTMENT
    assert result["confidence"] == 0.0


def test_low_confidence_uses_default(db):
    seed_departments(db)
    result = department_for(db, "pothole", confidence=0.1, threshold=0.4)
    assert result["name"] == DEFAULT_DEPARTMENT
