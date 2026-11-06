import requests
from sqlalchemy import select

from app.models import RawDocument
from app.models.enums import ScrapeStatus
from app.scraping import fetch_contacts
from app.scraping.fetch_contacts import SITE


class FakeRobots:
    def __init__(self, blocked=()):
        self.blocked = blocked

    def can_fetch(self, agent, url):
        return not any(part in url for part in self.blocked)


def page_with_links(*hrefs):
    anchors = "".join(f'<a href="{href}">x</a>' for href in hrefs)
    return f"<html><body>{anchors}</body></html>"


def use_site(monkeypatch, pages, blocked=()):
    asked = []

    def fake_get_page(session, url):
        asked.append(url)
        result = pages.get(url)
        if result is None:
            raise requests.HTTPError("404 not found")
        return result, "text/html; charset=utf-8"

    monkeypatch.setattr(fetch_contacts, "get_page", fake_get_page)
    monkeypatch.setattr(
        fetch_contacts, "read_robots", lambda session: FakeRobots(blocked)
    )
    monkeypatch.setattr(fetch_contacts.time, "sleep", lambda seconds: None)
    return asked


def stored_urls(db, run):
    rows = db.scalars(
        select(RawDocument).where(RawDocument.scrape_run_id == run.id)
    ).all()
    return [row.source_url for row in rows]


def test_links_are_limited_to_contact_pages_on_the_same_site():
    html = page_with_links(
        "/Senior_Officers?page=2",
        "/senior_officers?page=2#top",
        "/Specialunitsinfo?specialunits_category=4",
        "/about-us",
        "https://example.com/impcontacts",
        "mailto:someone@example.com",
    )

    links = fetch_contacts.find_contact_links(html, SITE + "/impcontacts")

    assert links == [
        SITE + "/Senior_Officers?page=2",
        SITE + "/senior_officers?page=2",
        SITE + "/Specialunitsinfo?specialunits_category=4",
    ]


def test_run_stores_start_pages_and_one_level_of_links(db, monkeypatch):
    start_urls = [SITE + path for path in fetch_contacts.START_PATHS]
    pages = {url: page_with_links() for url in start_urls}
    extra = SITE + "/impcontacts?page=2"
    pages[start_urls[0]] = page_with_links("/impcontacts?page=2")
    pages[extra] = page_with_links("/impcontacts?page=3")
    asked = use_site(monkeypatch, pages)

    run = fetch_contacts.run_fetch(db, session=None)

    assert run.status == ScrapeStatus.SUCCEEDED
    assert run.rows_added == 6
    assert run.pages_failed == 0
    assert stored_urls(db, run) == start_urls + [extra]
    assert SITE + "/impcontacts?page=3" not in asked


def test_failed_page_is_counted_and_the_rest_continue(db, monkeypatch):
    start_urls = [SITE + path for path in fetch_contacts.START_PATHS]
    pages = {url: page_with_links() for url in start_urls}
    del pages[start_urls[1]]
    use_site(monkeypatch, pages)

    run = fetch_contacts.run_fetch(db, session=None)

    assert run.status == ScrapeStatus.SUCCEEDED
    assert run.rows_added == 4
    assert run.pages_failed == 1
    assert start_urls[1] not in stored_urls(db, run)


def test_page_limit_stops_the_crawl(db, monkeypatch):
    start_urls = [SITE + path for path in fetch_contacts.START_PATHS]
    many = [f"/impcontacts?page={n}" for n in range(2, 60)]
    pages = {url: page_with_links(*many) for url in start_urls}
    pages.update({SITE + path: page_with_links() for path in many})
    use_site(monkeypatch, pages)

    run = fetch_contacts.run_fetch(db, session=None)

    assert run.rows_added == fetch_contacts.PAGE_LIMIT


def test_robots_blocked_pages_are_never_requested(db, monkeypatch):
    start_urls = [SITE + path for path in fetch_contacts.START_PATHS]
    pages = {url: page_with_links() for url in start_urls}
    asked = use_site(monkeypatch, pages, blocked=["Senior_Officers"])

    run = fetch_contacts.run_fetch(db, session=None)

    assert SITE + "/Senior_Officers" not in asked
    assert run.rows_added == 4
    assert run.pages_failed == 0
    assert "1 blocked" in run.summary


def test_run_fails_when_nothing_could_be_stored(db, monkeypatch):
    use_site(monkeypatch, {})

    run = fetch_contacts.run_fetch(db, session=None)

    assert run.status == ScrapeStatus.FAILED
    assert run.rows_added == 0
    assert run.pages_failed == len(fetch_contacts.START_PATHS)
    assert run.error_message


def test_non_html_response_counts_as_failed(monkeypatch):
    class Reply:
        text = "%PDF"
        headers = {"Content-Type": "application/pdf"}

        def raise_for_status(self):
            pass

    class Session:
        def get(self, url, timeout):
            return Reply()

    try:
        fetch_contacts.get_page(Session(), SITE + "/impcontacts")
    except ValueError as error:
        assert "not an HTML page" in str(error)
    else:
        raise AssertionError("expected ValueError")
