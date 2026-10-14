from geoalchemy2 import WKTElement
from sqlalchemy import func, select

from app.models import Authority, Department, JurisdictionArea


def box(west, south, east, north):
    corners = [(west, south), (east, south), (east, north), (west, north)]
    ring = ", ".join(f"{x} {y}" for x, y in corners + corners[:1])
    return f"MULTIPOLYGON((({ring})))"


# roughly 1 km square in Powai, not a real boundary
SQUARE = box(72.90, 19.13, 72.91, 19.14)


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

    assert covering(db, 72.905, 19.135) == ["campus"]
    assert covering(db, 72.92, 19.135) == []


def test_point_on_the_boundary_counts_as_inside(db):
    add_area(db, "campus", SQUARE, 20)

    assert covering(db, 72.90, 19.135) == ["campus"]


def test_overlapping_areas_come_back_highest_priority_first(db):
    add_area(db, "ward", box(72.88, 19.11, 72.93, 19.16), 10)
    add_area(db, "campus", SQUARE, 20)

    assert covering(db, 72.905, 19.135) == ["campus", "ward"]
    assert covering(db, 72.885, 19.115) == ["ward"]


def test_deleting_an_authority_removes_its_areas(db):
    add_area(db, "campus", SQUARE, 20)
    authority = db.scalar(select(Authority).where(Authority.name == "campus"))

    db.delete(authority)
    db.flush()

    assert db.scalar(select(func.count()).select_from(JurisdictionArea)) == 0
