import json
import sys
from datetime import datetime, timezone

import osm2geojson
from shapely.geometry import shape
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.models import Authority, Jurisdiction, RawDocument, ScrapeRun
from app.models.enums import JurisdictionStatus, ScrapeStatus
from app.scraping.fetch_boundaries import SOURCE_NAME as FETCH_SOURCE
from app.scraping.fetch_boundaries import WARD_LEVEL, fail_run

LOAD_SOURCE = "osm_mumbai_wards_load"
AUTHORITY_NAME = "Brihanmumbai Municipal Corporation"
AUTHORITY_AREA = "Mumbai"
WARD_TYPE = "ward"
WARD_PRIORITY = 10
MIN_LNG, MAX_LNG = 72.7, 73.1
MIN_LAT, MAX_LAT = 18.85, 19.35


def find_raw_text(db):
    latest_run = db.scalars(
        select(ScrapeRun)
        .where(
            ScrapeRun.source == FETCH_SOURCE,
            ScrapeRun.status == ScrapeStatus.SUCCEEDED,
        )
        .order_by(ScrapeRun.id.desc())
    ).first()

    if latest_run is None:
        return None

    document = db.scalars(
        select(RawDocument).where(RawDocument.scrape_run_id == latest_run.id)
    ).first()

    if document is None:
        return None

    return document.content


def in_mumbai(geometry):
    min_lng, min_lat, max_lng, max_lat = shape(geometry).bounds
    return (
        MIN_LNG <= min_lng
        and max_lng <= MAX_LNG
        and MIN_LAT <= min_lat
        and max_lat <= MAX_LAT
    )


def clean_features(features):
    wards = []
    seen_ids = set()
    counts = {"not_ward": 0, "duplicate": 0, "outside_mumbai": 0, "invalid": 0}

    for feature in features:
        properties = feature["properties"]
        tags = properties.get("tags", {})
        geometry = feature["geometry"]

        is_polygon = geometry["type"] in ("Polygon", "MultiPolygon")
        if tags.get("admin_level") != WARD_LEVEL or not is_polygon:
            counts["not_ward"] += 1
            continue
        if properties["id"] in seen_ids:
            counts["duplicate"] += 1
            continue
        if not in_mumbai(geometry):
            counts["outside_mumbai"] += 1
            continue

        seen_ids.add(properties["id"])
        if not shape(geometry).is_valid:
            counts["invalid"] += 1
        wards.append(
            {
                "osm_id": properties["id"],
                "name": tags.get("name", "unnamed"),
                "ward_code": tags.get("ref"),
                "geometry": json.dumps(geometry),
            }
        )
    return wards, counts


def find_authority(db):
    authority = db.scalars(
        select(Authority).where(Authority.name == AUTHORITY_NAME)
    ).first()
    if authority is None:
        authority = Authority(name=AUTHORITY_NAME, jurisdiction=AUTHORITY_AREA)
        db.add(authority)
        db.flush()
    return authority


def save_wards(db, wards, authority):
    added = 0
    updated = 0
    for ward in wards:
        row = db.scalars(
            select(Jurisdiction).where(Jurisdiction.osm_id == ward["osm_id"])
        ).first()
        if row is None:
            row = Jurisdiction(osm_id=ward["osm_id"])
            db.add(row)
            added += 1
        else:
            updated += 1

        row.name = ward["name"]
        row.ward_code = ward["ward_code"]
        row.type = WARD_TYPE
        row.authority_id = authority.id
        row.priority = WARD_PRIORITY
        row.source = "osm"
        row.status = JurisdictionStatus.APPROVED

        boundary = func.ST_GeomFromGeoJSON(ward["geometry"])
        boundary = func.ST_SetSRID(boundary, 4326)
        boundary = func.ST_MakeValid(boundary)
        boundary = func.ST_CollectionExtract(boundary, 3)
        boundary = func.ST_Multi(boundary)

        row.boundary = boundary
    db.flush()
    return added, updated


def count_invalid_wards(db):
    return db.scalar(
        select(func.count())
        .select_from(Jurisdiction)
        .where(
            Jurisdiction.type == WARD_TYPE,
            Jurisdiction.osm_id.is_not(None),
            ~func.ST_IsValid(Jurisdiction.boundary),
        )
    )


def run_load(db):
    run = ScrapeRun(source=LOAD_SOURCE, status=ScrapeStatus.RUNNING)
    db.add(run)
    db.commit()

    text = find_raw_text(db)
    if text is None:
        fail_run(db, run, "no successful boundary fetch found, run fetch first")
        return run

    features = osm2geojson.json2geojson(json.loads(text))["features"]
    wards, counts = clean_features(features)
    if not wards:
        fail_run(db, run, "no ward polygons left after cleaning")
        return run

    authority = find_authority(db)
    added, updated = save_wards(db, wards, authority)

    still_invalid = count_invalid_wards(db)
    if still_invalid:
        db.rollback()
        fail_run(db, run, f"{still_invalid} wards still invalid after ST_MakeValid")
        return run

    run.summary = (
        f"{len(wards)} wards kept ({added} added, {updated} updated). "
        f"Dropped: {counts['not_ward']} not wards, {counts['duplicate']} duplicates, "
        f"{counts['outside_mumbai']} outside Mumbai. "
        f"{counts['invalid']} had invalid shapes and were repaired."
    )
    run.rows_added = added
    run.status = ScrapeStatus.SUCCEEDED
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    print(run.summary)
    return run


def main():
    db = SessionLocal()
    try:
        run = run_load(db)
        failed = run.status == ScrapeStatus.FAILED
    finally:
        db.close()
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
