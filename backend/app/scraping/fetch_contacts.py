import sys
import time
from datetime import datetime, timezone
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from app.core.db import SessionLocal
from app.models import RawDocument, ScrapeRun
from app.models.enums import ScrapeStatus

SITE = "https://mumbaipolice.gov.in"
SOURCE_NAME = "mumbai_police_contacts"
USER_AGENT = "CivicSense-student-project (course project, IIT Bombay)"
START_PATHS = [
    "/impcontacts",
    "/Senior_Officers",
    "/Divisional_officers",
    "/Police_incharge",
    "/Specialunitsinfo?specialunits_category=1",
]
PAGE_LIMIT = 30
PAUSE_SECONDS = 2
TIMEOUT_SECONDS = 30

CONTACT_PATHS = {urlparse(path).path.lower() for path in START_PATHS}


def read_robots(session):
    rules = RobotFileParser()
    try:
        response = session.get(SITE + "/robots.txt", timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        rules.disallow_all = True
        return rules

    if response.status_code == 200:
        rules.parse(response.text.splitlines())
    elif response.status_code in (404, 410):
        rules.parse([])
    else:
        rules.disallow_all = True
    return rules


def get_page(session, url):
    response = session.get(url, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type.lower():
        raise ValueError(f"not an HTML page ({content_type or 'no content type'})")
    return response.text, content_type


def find_contact_links(html, page_url):
    site_host = urlparse(SITE).netloc
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        link, _ = urldefrag(urljoin(page_url, anchor["href"].strip()))
        parts = urlparse(link)
        if parts.scheme not in ("http", "https") or parts.netloc != site_host:
            continue
        if parts.path.lower() in CONTACT_PATHS and link not in links:
            links.append(link)
    return links


def finish_run(db, run, stored, failed, skipped):
    run.rows_added = stored
    run.pages_failed = failed
    run.summary = f"{stored} stored, {failed} failed, {skipped} blocked by robots.txt"
    run.finished_at = datetime.now(timezone.utc)
    if stored:
        run.status = ScrapeStatus.SUCCEEDED
    else:
        run.status = ScrapeStatus.FAILED
        run.error_message = "no page could be stored"
    db.commit()


def run_fetch(db, session):
    run = ScrapeRun(source=SOURCE_NAME, status=ScrapeStatus.RUNNING)
    db.add(run)
    db.commit()

    robots = read_robots(session)
    queue = [(SITE + path, 0) for path in START_PATHS]
    queued = {url for url, _ in queue}
    tried = stored = failed = skipped = 0

    while queue and tried < PAGE_LIMIT:
        url, depth = queue.pop(0)
        if not robots.can_fetch(USER_AGENT, url):
            print(f"blocked by robots.txt: {url}")
            skipped += 1
            continue

        time.sleep(PAUSE_SECONDS)
        tried += 1
        try:
            html, content_type = get_page(session, url)
        except (requests.RequestException, ValueError) as error:
            print(f"failed: {url} ({error})")
            failed += 1
            continue

        db.add(
            RawDocument(
                scrape_run_id=run.id,
                source_url=url,
                content_type=content_type,
                content=html,
            )
        )
        db.commit()
        stored += 1
        print(f"stored: {url}")

        if depth == 0:
            for link in find_contact_links(html, url):
                if link not in queued:
                    queued.add(link)
                    queue.append((link, 1))

    finish_run(db, run, stored, failed, skipped)
    return run


def main():
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    db = SessionLocal()
    try:
        run = run_fetch(db, session)
        print(run.summary)
        nothing_stored = run.status == ScrapeStatus.FAILED
    finally:
        db.close()
        session.close()
    if nothing_stored:
        sys.exit(1)


if __name__ == "__main__":
    main()
