import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from app.core.db import SessionLocal
from app.models import RawDocument, ScrapeRun
from app.models.enums import ScrapeStatus
from app.scraping.fetch_boundaries import fail_run

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SOURCE_NAME = "osm_mumbai_special_areas"
USER_AGENT = "CivicSense"
TIMEOUT_SECONDS = 180
EXTRA_TRIES = 2
WAIT_SECONDS = 30

TAG_TYPES = [
    ("amenity", "university", "university"),
    ("amenity", "college", "college"),
    ("aeroway", "aerodrome", "airport"),
    ("landuse", "military", "military"),
    ("landuse", "railway", "railway"),
    ("landuse", "industrial", "industrial"),
]

QUERY = """[out:json][timeout:180][bbox:18.85,72.7,19.35,73.1];
(
  nwr["amenity"="university"];
  nwr["amenity"="college"];
  nwr["aeroway"="aerodrome"];
  nwr["landuse"="military"];
  nwr["landuse"="railway"];
  nwr["landuse"="industrial"];
);
out geom;"""


def download():
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    request = urllib.request.Request(
        OVERPASS_URL, data=body, headers={"User-Agent": USER_AGENT}
    )

    last_error = None
    for attempt in range(EXTRA_TRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                content_type = response.headers.get("Content-Type")
                text = response.read().decode("utf-8")
            return text, content_type
        except (OSError, ValueError) as error:
            last_error = error
            print(f"attempt {attempt + 1} failed: {error}")
            if attempt < EXTRA_TRIES:
                time.sleep(WAIT_SECONDS)
    raise last_error


def tag_type(tags):
    for key, value, type_name in TAG_TYPES:
        if tags.get(key) == value:
            return type_name
    return None


def find_area_names(text):
    data = json.loads(text)
    names = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        if tag_type(tags) is not None:
            names.append(tags.get("name", "unnamed"))
    return sorted(names)


def run_fetch(db):
    run = ScrapeRun(source=SOURCE_NAME, status=ScrapeStatus.RUNNING)
    db.add(run)
    db.commit()

    try:
        text, content_type = download()
    except OSError as error:
        fail_run(db, run, str(error))
        return run

    db.add(
        RawDocument(
            scrape_run_id=run.id,
            source_url=OVERPASS_URL,
            content_type=content_type,
            content=text,
        )
    )
    db.commit()

    try:
        area_names = find_area_names(text)
    except ValueError as error:
        fail_run(db, run, f"response was not valid JSON: {error}")
        return run

    if not area_names:
        fail_run(db, run, "no special areas in the response")
        return run

    run.rows_added = len(area_names)
    run.status = ScrapeStatus.SUCCEEDED
    run.finished_at = datetime.now(timezone.utc)
    db.commit()

    print(f"{len(area_names)} special areas came back:")
    for name in area_names:
        print(f"  {name}")
    return run


def main():
    db = SessionLocal()
    try:
        run = run_fetch(db)
        failed = run.status == ScrapeStatus.FAILED
    finally:
        db.close()
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
