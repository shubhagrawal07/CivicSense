import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from app.core.db import SessionLocal
from app.models import RawDocument, ScrapeRun
from app.models.enums import ScrapeStatus

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SOURCE_NAME = "osm_mumbai_wards"
USER_AGENT = "CivicSense"
TIMEOUT_SECONDS = 180
EXTRA_TRIES = 2
WAIT_SECONDS = 30
WARD_LEVEL = "10"

QUERY = """[out:json][timeout:180];
rel["name"~"^Mumbai (City|Suburban) District$"]["admin_level"="5"]->.districts;
.districts map_to_area->.districtareas;
(
  .districts;
  rel(area.districtareas)["boundary"~"administrative|local_authority"]["admin_level"="10"];
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


def find_ward_names(text):
    data = json.loads(text)
    names = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        if tags.get("admin_level") == WARD_LEVEL:
            names.append(tags.get("name", "unnamed"))
    return sorted(names)


def fail_run(db, run, message):
    print(f"fetch failed: {message}")
    run.status = ScrapeStatus.FAILED
    run.error_message = message
    run.finished_at = datetime.now(timezone.utc)
    db.commit()


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
        ward_names = find_ward_names(text)
    except ValueError as error:
        fail_run(db, run, f"response was not valid JSON: {error}")
        return run

    if not ward_names:
        fail_run(db, run, "no ward polygons in the response")
        return run

    run.rows_added = len(ward_names)
    run.status = ScrapeStatus.SUCCEEDED
    run.finished_at = datetime.now(timezone.utc)
    db.commit()

    print(f"{len(ward_names)} wards came back:")
    for name in ward_names:
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
