import json
from pathlib import Path

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import select

from app.models import Authority, AuthorityContact, Department, JurisdictionArea
from app.models.enums import ContactType, VerificationStatus
from app.seed import seed_authorities, seed_departments
from app.services.authority import lookup_authority

CAMPUS_FILE = Path(__file__).parents[1] / "app" / "seed_data" / "iitb_campus.geojson"
MAIN_BUILDING = (19.1334, 72.9133)
HIRANANDANI = (19.1176, 72.9060)


@pytest.fixture
def mumbai(db):
    seed_departments(db)
    seed_authorities(db)
    return db


def dept_id(db, name):
    return db.scalar(select(Department.id).where(Department.name == name))


def lookup(db, dept_name, point):
    return lookup_authority(db, dept_id(db, dept_name), *point)


def test_road_issue_on_campus_goes_to_iitb(mumbai):
    result = lookup(mumbai, "Roads / Public Works", MAIN_BUILDING)

    assert result.authority.name == "IIT Bombay Civil Maintenance"
    assert not result.is_fallback
    assert not result.needs_review
    assert result.other_matches == []
    assert result.contacts[0].verified


def test_road_issue_outside_campus_goes_to_bmc(mumbai):
    result = lookup(mumbai, "Roads / Public Works", HIRANANDANI)

    assert result.authority.name == "BMC Roads Department"
    assert not result.needs_review


def test_department_iitb_does_not_handle_stays_with_bmc_on_campus(mumbai):
    result = lookup(mumbai, "Drainage / Sewerage", MAIN_BUILDING)

    assert result.authority.name.startswith("BMC")


def test_point_on_the_campus_edge_asks_for_review(mumbai):
    collection = json.loads(CAMPUS_FILE.read_text())
    lng, lat = collection["features"][0]["geometry"]["coordinates"][0][0][0]

    result = lookup(mumbai, "Roads / Public Works", (lat, lng))

    assert result.needs_review
    names = {result.authority.name} | {a.name for a in result.other_matches}
    assert names == {"IIT Bombay Civil Maintenance", "BMC Roads Department"}


def test_department_with_no_authority_falls_back_to_unverified_general_contacts(
    mumbai,
):
    orphan = Department(name="Parks")
    mumbai.add(orphan)
    mumbai.flush()

    result = lookup_authority(mumbai, orphan.id, *MAIN_BUILDING)

    assert result.authority is None
    assert result.is_fallback
    assert {c.value for c in result.contacts} >= {"1916"}
    assert not any(c.verified for c in result.contacts)


# the tests below use made-up areas in Bengaluru so seed data cannot interfere
def box(west, south, east, north):
    corners = [(west, south), (east, south), (east, north), (west, north)]
    ring = ", ".join(f"{x} {y}" for x, y in corners + corners[:1])
    return WKTElement(f"MULTIPOLYGON((({ring})))", srid=4326)


def make_authority(db, dept, name, area=None, priority=0, contacts=()):
    authority = Authority(name=name, jurisdiction=name, department=dept)
    if area is not None:
        authority.areas.append(
            JurisdictionArea(label=name, area=area, priority=priority)
        )
    for kind, value, status in contacts:
        authority.contacts.append(
            AuthorityContact(type=kind, value=value, verification_status=status)
        )
    db.add(authority)
    db.flush()
    return authority


@pytest.fixture
def dept(db):
    dept = Department(name="Test roads")
    db.add(dept)
    db.flush()
    return dept


INSIDE = (12.975, 77.595)
BIG = box(77.57, 12.95, 77.62, 13.00)
SMALL = box(77.59, 12.97, 77.60, 12.98)


def test_higher_priority_area_wins_over_the_citywide_default(db, dept):
    make_authority(
        db,
        dept,
        "city",
        contacts=[(ContactType.HELPLINE, "1", VerificationStatus.UNVERIFIED)],
    )
    make_authority(db, dept, "ward", BIG, 10)
    campus = make_authority(db, dept, "campus", SMALL, 20)

    result = lookup_authority(db, dept.id, *INSIDE)

    assert result.authority is campus
    assert not result.needs_review


def test_equal_priority_overlap_is_flagged_and_lowest_id_wins(db, dept):
    first = make_authority(db, dept, "first", SMALL, 10)
    second = make_authority(db, dept, "second", SMALL, 10)

    result = lookup_authority(db, dept.id, *INSIDE)

    assert result.authority is first
    assert result.needs_review
    assert result.other_matches == [second]


def test_unverified_contacts_come_after_verified_ones(db, dept):
    make_authority(
        db,
        dept,
        "city",
        contacts=[
            (ContactType.HELPLINE, "unverified", VerificationStatus.UNVERIFIED),
            (ContactType.WEBSITE, "verified", VerificationStatus.VERIFIED),
        ],
    )

    result = lookup_authority(db, dept.id, *INSIDE)

    assert [c.value for c in result.contacts] == ["verified", "unverified"]
    assert [c.verified for c in result.contacts] == [True, False]


def test_authority_without_contacts_uses_the_fallback(mumbai, dept):
    authority = make_authority(mumbai, dept, "city")

    result = lookup_authority(mumbai, dept.id, *INSIDE)

    assert result.authority is authority
    assert result.is_fallback
    assert result.contacts
    assert not any(c.verified for c in result.contacts)
