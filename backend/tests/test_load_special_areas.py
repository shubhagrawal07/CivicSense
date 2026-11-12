import json

from sqlalchemy import func, select

from app.models import Jurisdiction, RawDocument, ScrapeRun
from app.models.enums import JurisdictionStatus, ScrapeStatus
from app.scraping import fetch_special_areas, load_special_areas

UNIVERSITY_ID = 991001
AIRPORT_ID = 991002
TINY_ID = 991003
SHOP_ID = 991004


def square(west, south, east, north):
    corners = [
        (west, south),
        (east, south),
        (east, north),
        (west, north),
        (west, south),
    ]
    return [{"lat": lat, "lon": lng} for lng, lat in corners]


def way(osm_id, name, tags, points):
    all_tags = dict(tags)
    all_tags["name"] = name
    return {"type": "way", "id": osm_id, "tags": all_tags, "geometry": points}


def sample_response():
    university = way(
        UNIVERSITY_ID,
        "Test University",
        {"amenity": "university"},
        square(72.90, 19.00, 72.91, 19.01),
    )
    airport = way(
        AIRPORT_ID,
        "Test Airport",
        {"aeroway": "aerodrome"},
        square(72.80, 19.05, 72.82, 19.07),
    )
    tiny = way(
        TINY_ID,
        "Tiny Industrial Sliver",
        {"landuse": "industrial"},
        square(72.95, 19.10, 72.9501, 19.1001),
    )
    shop = way(
        SHOP_ID,
        "Test Shop",
        {"shop": "supermarket"},
        square(72.85, 19.02, 72.86, 19.03),
    )
    return json.dumps({"elements": [university, airport, tiny, shop]})


def add_fetch_run(db):
    run = ScrapeRun(
        source=fetch_special_areas.SOURCE_NAME, status=ScrapeStatus.SUCCEEDED
    )
    db.add(run)
    db.flush()
    db.add(
        RawDocument(
            scrape_run_id=run.id,
            source_url=fetch_special_areas.OVERPASS_URL,
            content=sample_response(),
        )
    )
    db.flush()


def count_test_areas(db):
    return db.scalar(
        select(func.count())
        .select_from(Jurisdiction)
        .where(Jurisdiction.osm_id.in_([UNIVERSITY_ID, AIRPORT_ID, TINY_ID, SHOP_ID]))
    )


def test_only_special_areas_are_loaded_and_rerun_adds_nothing(db):
    add_fetch_run(db)

    first = load_special_areas.run_load(db)
    second = load_special_areas.run_load(db)

    assert first.status == ScrapeStatus.SUCCEEDED
    assert second.status == ScrapeStatus.SUCCEEDED
    assert first.rows_added == 2
    assert second.rows_added == 0
    assert count_test_areas(db) == 2
    assert "1 not special" in first.summary
    assert "1 too small" in first.summary


def test_loaded_areas_are_valid_candidates_without_an_authority(db):
    add_fetch_run(db)
    load_special_areas.run_load(db)

    university = db.scalars(
        select(Jurisdiction).where(Jurisdiction.osm_id == UNIVERSITY_ID)
    ).one()
    inside = func.ST_SetSRID(func.ST_MakePoint(72.905, 19.005), 4326)
    outside = func.ST_SetSRID(func.ST_MakePoint(72.70, 18.90), 4326)

    assert db.scalar(select(func.ST_IsValid(university.boundary)))
    assert db.scalar(select(func.ST_Contains(university.boundary, inside)))
    assert not db.scalar(select(func.ST_Contains(university.boundary, outside)))
    assert university.type == "university"
    assert university.status == JurisdictionStatus.CANDIDATE
    assert university.authority_id is None

    airport = db.scalars(
        select(Jurisdiction).where(Jurisdiction.osm_id == AIRPORT_ID)
    ).one()
    assert airport.type == "airport"
