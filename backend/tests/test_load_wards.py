import json

from sqlalchemy import func, select

from app.models import Jurisdiction, RawDocument, ScrapeRun
from app.models.enums import ScrapeStatus
from app.scraping import fetch_boundaries, load_wards

WARD_ID = 990001
DISTRICT_ID = 990002


def square(west, south, east, north):
    corners = [
        (west, south),
        (east, south),
        (east, north),
        (west, north),
        (west, south),
    ]
    return [{"lat": lat, "lon": lng} for lng, lat in corners]


def relation(osm_id, name, level, points):
    return {
        "type": "relation",
        "id": osm_id,
        "tags": {
            "name": name,
            "admin_level": level,
            "type": "boundary",
            "boundary": "administrative",
        },
        "members": [
            {"type": "way", "ref": osm_id + 1000, "role": "outer", "geometry": points}
        ],
    }


def sample_response():
    ward = relation(WARD_ID, "Test Ward", "10", square(72.80, 19.00, 72.82, 19.02))
    district = relation(
        DISTRICT_ID, "Test District", "5", square(72.70, 18.90, 72.90, 19.10)
    )
    return json.dumps({"elements": [ward, district]})


def add_fetch_run(db):
    run = ScrapeRun(source=fetch_boundaries.SOURCE_NAME, status=ScrapeStatus.SUCCEEDED)
    db.add(run)
    db.flush()
    db.add(
        RawDocument(
            scrape_run_id=run.id,
            source_url=fetch_boundaries.OVERPASS_URL,
            content=sample_response(),
        )
    )
    db.flush()


def count_test_wards(db):
    return db.scalar(
        select(func.count())
        .select_from(Jurisdiction)
        .where(Jurisdiction.osm_id.in_([WARD_ID, DISTRICT_ID]))
    )


def test_only_wards_are_loaded_and_rerun_adds_nothing(db):
    add_fetch_run(db)

    first = load_wards.run_load(db)
    second = load_wards.run_load(db)

    assert first.status == ScrapeStatus.SUCCEEDED
    assert second.status == ScrapeStatus.SUCCEEDED
    assert first.rows_added == 1
    assert second.rows_added == 0
    assert count_test_wards(db) == 1
    assert "1 not wards" in first.summary


def test_loaded_ward_is_valid_and_contains_its_points(db):
    add_fetch_run(db)
    load_wards.run_load(db)

    ward = db.scalars(select(Jurisdiction).where(Jurisdiction.osm_id == WARD_ID)).one()
    inside = func.ST_SetSRID(func.ST_MakePoint(72.81, 19.01), 4326)
    outside = func.ST_SetSRID(func.ST_MakePoint(72.85, 19.05), 4326)

    assert db.scalar(select(func.ST_IsValid(ward.boundary)))
    assert db.scalar(select(func.ST_Contains(ward.boundary, inside)))
    assert not db.scalar(select(func.ST_Contains(ward.boundary, outside)))
    assert ward.authority_id is not None
    assert ward.priority == load_wards.WARD_PRIORITY
