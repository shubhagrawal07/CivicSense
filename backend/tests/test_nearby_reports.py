from geoalchemy2 import Geography, WKTElement
from sqlalchemy import cast, func, select

from app.models import Report, User

CENTER = (72.8777, 19.0760)


def make_report(user_id, lon, lat):
    return Report(
        user_id=user_id,
        description="test",
        location=WKTElement(f"POINT({lon} {lat})", srid=4326),
    )


def nearby_ids(db, lon, lat, metres):
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    stmt = select(Report.id).where(
        func.ST_DWithin(
            cast(Report.location, Geography), cast(point, Geography), metres
        )
    )
    return set(db.scalars(stmt))


def test_only_reports_within_500m_are_returned(db):
    user = User(name="t", email="t@example.com", password_hash="x")
    db.add(user)
    db.flush()

    lon, lat = CENTER
    same_spot = make_report(user.id, lon, lat)
    about_330m = make_report(user.id, lon, lat + 0.003)
    about_670m = make_report(user.id, lon, lat + 0.006)
    other_city = make_report(user.id, 77.5946, 12.9716)
    db.add_all([same_spot, about_330m, about_670m, other_city])
    db.flush()

    found = nearby_ids(db, lon, lat, 500)

    assert found == {same_spot.id, about_330m.id}
