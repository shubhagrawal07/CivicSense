import json
import sys
from datetime import datetime, timezone

import osm2geojson
from shapely.geometry import shape
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.models import Jurisdiction, RawDocument, ScrapeRun
from app.models.enums import JurisdictionStatus, ScrapeStatus
from app.scraping.fetch_boundaries import fail_run
from app.scraping.fetch_special_areas import SOURCE_NAME as FETCH_SOURCE
from app.scraping.fetch_special_areas import TAG_TYPES, tag_type
from app.scraping.load_wards import in_mumbai

LOAD_SOURCE = "osm_mumbai_special_areas_load"
MIN_AREA_SQM = 1000
METERS_PER_DEGREE = 111320


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


def approx_area_sqm(geometry):
    polygon = shape(geometry)
    return polygon.area * METERS_PER_DEGREE * METERS_PER_DEGREE


def clean_features(features):
    areas = []
    seen_ids = set()
    counts = {
        "not_special": 0,
        "duplicate": 0,
        "outside_mumbai": 0,
        "too_small": 0,
        "invalid": 0,
    }

    for feature in features:
        properties = feature["properties"]
        tags = properties.get("tags", {})
        geometry = feature["geometry"]

        type_name = tag_type(tags)
        is_polygon = geometry["type"] in ("Polygon", "MultiPolygon")
        if type_name is None or not is_polygon:
            counts["not_special"] += 1
            continue
        if properties["id"] in seen_ids:
            counts["duplicate"] += 1
            continue
        if not in_mumbai(geometry):
            counts["outside_mumbai"] += 1
            continue
        if approx_area_sqm(geometry) < MIN_AREA_SQM:
            counts["too_small"] += 1
            continue

        seen_ids.add(properties["id"])
        if not shape(geometry).is_valid:
            counts["invalid"] += 1
        areas.append(
            {
                "osm_id": properties["id"],
                "name": tags.get("name", "unnamed"),
                "type": type_name,
                "geometry": json.dumps(geometry),
            }
        )
    return areas, counts


def save_areas(db, areas):
    added = 0
    updated = 0
    for area in areas:
        row = db.scalars(
            select(Jurisdiction).where(Jurisdiction.osm_id == area["osm_id"])
        ).first()
        if row is None:
            row = Jurisdiction(osm_id=area["osm_id"])
            db.add(row)
            added += 1
        else:
            updated += 1

        row.name = area["name"]
        row.type = area["type"]
        row.source = "osm"
        row.status = JurisdictionStatus.CANDIDATE

        boundary = func.ST_GeomFromGeoJSON(area["geometry"])
        boundary = func.ST_SetSRID(boundary, 4326)
        boundary = func.ST_MakeValid(boundary)
        boundary = func.ST_CollectionExtract(boundary, 3)
        boundary = func.ST_Multi(boundary)

        row.boundary = boundary
    db.flush()
    return added, updated


def count_invalid_areas(db):
    type_names = [type_name for _, _, type_name in TAG_TYPES]
    return db.scalar(
        select(func.count())
        .select_from(Jurisdiction)
        .where(
            Jurisdiction.type.in_(type_names),
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
        fail_run(db, run, "no successful special area fetch found, run fetch first")
        return run

    features = osm2geojson.json2geojson(json.loads(text))["features"]
    areas, counts = clean_features(features)
    if not areas:
        fail_run(db, run, "no special areas left after cleaning")
        return run

    added, updated = save_areas(db, areas)

    still_invalid = count_invalid_areas(db)
    if still_invalid:
        db.rollback()
        fail_run(db, run, f"{still_invalid} areas still invalid after ST_MakeValid")
        return run

    per_type = {}
    for area in areas:
        per_type[area["type"]] = per_type.get(area["type"], 0) + 1
    type_summary = ", ".join(f"{count} {name}" for name, count in per_type.items())

    run.summary = (
        f"{len(areas)} special areas kept ({added} added, {updated} updated): "
        f"{type_summary}. "
        f"Dropped: {counts['not_special']} not special, "
        f"{counts['duplicate']} duplicates, "
        f"{counts['outside_mumbai']} outside Mumbai, "
        f"{counts['too_small']} too small. "
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
