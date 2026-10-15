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
