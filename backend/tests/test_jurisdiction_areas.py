from geoalchemy2 import WKTElement
from sqlalchemy import func, select

from app.models import Authority, Department, JurisdictionArea
from app.models.enums import VerificationStatus
from app.seed import seed_authorities, seed_departments


def box(west, south, east, north):
    corners = [(west, south), (east, south), (east, north), (west, north)]
    ring = ", ".join(f"{x} {y}" for x, y in corners + corners[:1])
    return f"MULTIPOLYGON((({ring})))"


# roughly 1 km square placed in Bengaluru so it never overlaps the seeded
# Mumbai areas, not a real boundary
SQUARE = box(77.59, 12.97, 77.60, 12.98)


def point(lon, lat):
    return func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)


def covering(db, lon, lat):
    stmt = (
        select(JurisdictionArea.label)
        .where(func.ST_Covers(JurisdictionArea.area, point(lon, lat)))
        .order_by(JurisdictionArea.priority.desc())
    )
    return list(db.scalars(stmt))


def add_area(db, label, wkt, priority):
    dept = Department(name=f"test dept {label}")
    authority = Authority(name=label, jurisdiction=label, department=dept)
    authority.areas.append(
        JurisdictionArea(
            label=label, area=WKTElement(wkt, srid=4326), priority=priority
        )
    )
    db.add(authority)
    db.flush()


def test_point_inside_and_outside_an_area(db):
    add_area(db, "campus", SQUARE, 20)

    assert covering(db, 77.595, 12.975) == ["campus"]
    assert covering(db, 77.61, 12.975) == []


def test_point_on_the_boundary_counts_as_inside(db):
    add_area(db, "campus", SQUARE, 20)

    assert covering(db, 77.59, 12.975) == ["campus"]


def test_overlapping_areas_come_back_highest_priority_first(db):
    add_area(db, "ward", box(77.57, 12.95, 77.62, 13.00), 10)
    add_area(db, "campus", SQUARE, 20)

    assert covering(db, 77.595, 12.975) == ["campus", "ward"]
    assert covering(db, 77.575, 12.955) == ["ward"]


def test_deleting_an_authority_removes_its_areas(db):
    add_area(db, "campus", SQUARE, 20)
    authority = db.scalar(select(Authority).where(Authority.name == "campus"))

    db.delete(authority)
    db.flush()

    left = db.scalar(
        select(func.count())
        .select_from(JurisdictionArea)
        .where(JurisdictionArea.label == "campus")
    )
    assert left == 0


def seeded_iitb(db):
    seed_departments(db)
    seed_authorities(db)
    return db.scalars(
        select(JurisdictionArea).where(JurisdictionArea.label == "IIT Bombay campus")
    ).first()


def test_seeded_iitb_campus_area_is_valid_and_unverified(db):
    area = seeded_iitb(db)

    assert area.priority == 20
    assert area.verification_status == VerificationStatus.UNVERIFIED
    assert area.source_url
    assert db.scalar(select(func.ST_IsValid(area.area)))
    assert db.scalar(select(func.ST_NumGeometries(area.area))) == 2


def test_iitb_area_covers_the_campus_and_not_its_neighbours(db):
    seeded_iitb(db)

    main_building = (72.9133, 19.1334)
    hiranandani = (72.9060, 19.1176)
    assert set(covering(db, *main_building)) == {"IIT Bombay campus"}
    assert covering(db, *hiranandani) == []


def test_iitb_authorities_map_to_our_departments(db):
    seeded_iitb(db)

    rows = db.execute(
        select(Authority.name, Department.name)
        .join(Department)
        .where(Authority.name.like("IIT Bombay%"))
    ).all()
    assert dict(rows) == {
        "IIT Bombay Civil Maintenance": "Roads / Public Works",
        "IIT Bombay Public Health Office": "Sanitation / Solid Waste",
        "IIT Bombay Electrical Maintenance": "Electricity",
        "IIT Bombay Campus Administration": "General Grievance",
    }


def test_every_iitb_authority_has_the_campus_area_and_the_portal(db):
    seeded_iitb(db)

    authorities = db.scalars(
        select(Authority).where(Authority.name.like("IIT Bombay%"))
    ).all()
    for authority in authorities:
        assert [a.label for a in authority.areas] == ["IIT Bombay campus"]
        kinds = {c.type.value for c in authority.contacts}
        assert "COMPLAINT_PORTAL" in kinds
