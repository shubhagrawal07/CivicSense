import sys
import time
import urllib.robotparser
from datetime import datetime, timezone
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.core.db import SessionLocal
from app.models import RawDocument, ScrapeRun
from app.models.enums import ScrapeStatus

SITE = "https://mumbaipolice.gov.in"
SOURCE_NAME = "mumbai_police_contacts"
USER_AGENT = "CivicSense-student-project (course project, IIT Bombay)"
DELAY_SECONDS = 2
TIMEOUT_SECONDS = 30
PAGE_LIMIT = 30

START_PATHS = [
    "/impcontacts",
    "/Senior_Officers",
    "/Divisional_officers",
    "/Police_incharge",
    "/Specialunitsinfo?specialunits_category=1",
]

# only these pages are followed from the start pages
FOLLOW_PATHS = {
    "/impcontacts",
    "/senior_officers",
    "/divisional_officers",
    "/police_incharge",
    "/specialunitsinfo",
}


def load_robots():
    parser = urllib.robotparser.RobotFileParser()
    response = requests.get(
        f"{SITE}/robots.txt",
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS,
    )
    # a missing robots.txt means nothing is disallowed
    if response.status_code == 200:
        parser.parse(response.text.splitlines())
    else:
        parser.parse([])
    print(f"robots.txt answered {response.status_code}")
    return parser


def wanted_links(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for tag in soup.find_all("a", href=True):
        url, _ = urldefrag(urljoin(page_url, tag["href"]))
        parts = urlparse(url)
        if parts.netloc != urlparse(SITE).netloc:
            continue
        if parts.path.lower() in FOLLOW_PATHS:
            found.append(url)
    return found


def fetch(session, url):
    response = session.get(url, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response


def run_fetch(db, robots):
    run = ScrapeRun(source=SOURCE_NAME, status=ScrapeStatus.RUNNING)
    db.add(run)
    db.commit()

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    queue = [SITE + path for path in START_PATHS]
    seen = set(queue)
    start_urls = set(queue)
    fetched = 0
    failed = 0

    while queue and fetched + failed < PAGE_LIMIT:
        url = queue.pop(0)
        if not robots.can_fetch(USER_AGENT, url):
            print(f"skipped (robots.txt): {url}")
            continue

        try:
            response = fetch(session, url)
        except requests.RequestException as error:
            failed += 1
            print(f"failed: {url} ({error})")
        else:
            db.add(
                RawDocument(
                    scrape_run_id=run.id,
                    source_url=url,
                    content_type=response.headers.get("Content-Type"),
                    content=response.text,
                )
            )
            db.commit()
            fetched += 1
            print(f"stored: {url}")

            # links are only read from the start pages, so the crawl is one level deep
            if url in start_urls:
                for link in wanted_links(response.text, url):
                    if link not in seen:
                        seen.add(link)
                        queue.append(link)

        time.sleep(DELAY_SECONDS)

    run.rows_added = fetched
    run.pages_failed = failed
    run.status = ScrapeStatus.SUCCEEDED if fetched else ScrapeStatus.FAILED
    if not fetched:
        run.error_message = "no page could be stored"
    run.finished_at = datetime.now(timezone.utc)
    db.commit()

    print(f"done: {fetched} stored, {failed} failed")
    return run


def main():
    robots = load_robots()
    db = SessionLocal()
    try:
        run = run_fetch(db, robots)
        ok = run.status == ScrapeStatus.SUCCEEDED
    finally:
        db.close()
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
