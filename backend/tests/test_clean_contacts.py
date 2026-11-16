from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from app.models import (
    Authority,
    AuthorityContact,
    Department,
    RawDocument,
    ScrapeRun,
)
from app.models.enums import ContactType, ScrapeStatus, VerificationStatus
from app.scraping import clean_contacts
from app.scraping.clean_contacts import (
    AUTHORITY_NAME,
    clean_email,
    clean_phone,
    extract,
    phone_type,
    pick_department,
    run_clean,
    split_emails,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("22620826", "+912222620826"),
        ("2262 0826", "+912222620826"),
        ("022-2262-0826", "+912222620826"),
        ("+91 98765 43210", "+919876543210"),
        ("09876543210", "+919876543210"),
        ("919876543210", "+919876543210"),
        ("1800 22 1234", "1800221234"),
        ("100", "100"),
        ("1090", "1090"),
    ],
)
def test_phone_numbers_are_normalised(raw, expected):
    assert clean_phone(raw) == (expected, None)


@pytest.mark.parametrize(
    "raw, reason",
    [
        ("---", "no digits"),
        ("12345", "wrong length"),
        ("123456789012345", "wrong length"),
        ("0000000000", "repeated digits"),
        ("1234567890", "unrecognised number"),
    ],
)
def test_bad_phone_numbers_are_dropped_with_a_reason(raw, reason):
    assert clean_phone(raw) == (None, reason)


def test_emergency_numbers_get_their_own_type():
    assert phone_type("100") == ContactType.EMERGENCY
    assert phone_type("+912222620826") == ContactType.HELPLINE
    assert phone_type("1090") == ContactType.HELPLINE


def test_emails_are_lowercased_and_deobfuscated():
    assert clean_email("Help.Desk@Example.ORG") == ("help.desk@example.org", None)
    assert split_emails("ps[dot]aarey[dash]mum[at]mahapolice[dot]gov[dot]in") == [
        "ps.aarey-mum@mahapolice.gov.in"
    ]


def test_one_mailto_can_hold_several_addresses_and_stray_text():
    raw = "mailto:⁠a[at]x[dot]org / b[at]y[dot]org   Address :- somewhere"
    assert split_emails(raw) == ["a@x.org", "b@y.org"]


def test_badly_shaped_emails_are_rejected():
    assert clean_email("not-an-email") == (None, "invalid email")
    assert clean_email("a@b") == (None, "invalid email")


def test_department_comes_from_keywords_with_a_general_fallback():
    assert pick_department("Water Supply Complaints") == "Water Supply"
    assert pick_department("Drainage and sewerage cell") == "Drainage / Sewerage"
    assert pick_department("Pothole helpline") == "Roads / Public Works"
    assert pick_department("Emergency Contacts | Mumbai Police") == "General Grievance"
    assert pick_department("Broadway office") == "General Grievance"


TABLE_PAGE = """
<html><head><title>Emergency Contacts | Mumbai Police</title></head><body>
<h1>Emergency Contacts</h1>
<table>
<tr><td><b>Name of office</b></td><td><b>Telephone number</b></td>
    <td><b>Fax number</b></td><td><b>Entension number.</b></td></tr>
<tr><td>Control Room</td><td>22621855 22621983</td><td>22633319</td><td>100</td></tr>
<tr><td>Infoline</td><td>1090</td><td>---</td><td>---</td></tr>
</table>
</body></html>
"""


def test_table_rows_give_one_phone_per_number_and_mark_fax():
    items = extract(TABLE_PAGE)
    phones = [(i.raw, i.label, i.skip) for i in items if i.kind == "phone"]
    assert phones == [
        ("22621855", "Control Room", None),
        ("22621983", "Control Room", None),
        ("22633319", "Control Room", "fax number"),
        ("1090", "Infoline", None),
    ]


CARD_PAGE = """
<html><head><title>Police Station Incharge | Mumbai Police</title></head><body>
<h1>Police Station Incharge</h1>
<div class="card-wrapper-sr">
  <div class="card-up">
    <h4 title="Some Person">Some Person</h4>
    <b><p>Sr.P.I.</p></b><b> ( Aarey )</b>
  </div>
  <div class="card-down">
    <div class="marg-10"><img src="img/lanlandSvg.svg">
      <a href="tel:29272485">29272485</a></div>
    <div class="marg-10"><img src="img/faxSvg.svg">
      <a href="tel:29272486">29272486</a></div>
    <div class="marg-10"><img src="img/mobSvg.svg">
      <a href="tel:+918976952425">8976952425</a></div>
    <!-- <div class="marg-10"><img src="img/lanlandSvg.svg">
      <a href="tel:22223333">22223333</a></div> -->
    <div class="marg-10"><img src="img/emailSvg.svg">
      <a href="mailto:ps[dot]aarey[dot]mum[at]mahapolice[dot]gov[dot]in">x</a></div>
  </div>
</div>
</body></html>
"""


def test_cards_keep_landline_and_email_and_leave_out_the_person():
    items = extract(CARD_PAGE)
    got = [(i.kind, i.raw, i.skip) for i in items]
    assert got == [
        ("phone", "29272485", None),
        ("phone", "29272486", "fax number"),
        ("phone", "+918976952425", "officer mobile"),
        ("email", "ps.aarey.mum@mahapolice.gov.in", None),
    ]
    assert {i.label for i in items} == {"Sr.P.I. (Aarey)"}
    assert not any("Some Person" in i.label for i in items)


def test_card_label_works_when_the_post_is_not_in_bold():
    html = """
    <div class="card-wrapper-sr">
      <div class="card-up"><h4>Some Person</h4><p>ACP ( COLABA DIVISION )</p></div>
      <div class="card-down">
        <div class="marg-10"><img src="img/lanlandSvg.svg">
          <a href="tel:22812696">x</a></div>
      </div>
    </div>"""
    items = extract(html)
    assert [i.label for i in items] == ["ACP (COLABA DIVISION)"]


LINK_PAGE = """
<html><head><title>Special Units | Mumbai Police</title></head><body>
<h2>Crime Branch</h2>
<p>Traffic WhatsApp Helpline : <a href="tel:8454999999">8454999999</a></p>
<a href="mailto:tips@example.org">write to us</a>
<a href="https://example.org/OnlineComplaints?ps_id=0">Online Complaint</a>
<a href="https://example.org/Alert_wall">Citizen Wall</a>
<a href="#">Complaint corner</a>
<a href="tel:">empty</a>
</body></html>
"""


def test_loose_links_give_phones_emails_and_complaint_portals_only():
    items = extract(LINK_PAGE)
    got = [(i.kind, i.raw, i.label) for i in items]
    assert got == [
        ("phone", "8454999999", "Traffic WhatsApp Helpline"),
        ("email", "tips@example.org", "Special Units"),
        ("portal", "https://example.org/OnlineComplaints?ps_id=0", "Online Complaint"),
    ]


def department(db, name):
    found = db.scalar(select(Department).where(Department.name == name))
    if found is None:
        found = Department(name=name)
        db.add(found)
        db.flush()
    return found


def store_page(db, run, url, html):
    doc = RawDocument(
        scrape_run_id=run.id,
        source_url=url,
        content_type="text/html",
        content=html,
        fetched_at=datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc),
    )
    db.add(doc)
    db.flush()
    return doc


@pytest.fixture
def pages(db, monkeypatch):
    department(db, "General Grievance")
    department(db, "Water Supply")
    run = ScrapeRun(source="test", status=ScrapeStatus.SUCCEEDED)
    db.add(run)
    db.flush()
    docs = []
    monkeypatch.setattr(clean_contacts, "latest_documents", lambda session: docs)
    return lambda url, html: docs.append(store_page(db, run, url, html))


def saved_contacts(db, urls):
    return db.scalars(
        select(AuthorityContact).where(AuthorityContact.source_url.in_(urls))
    ).all()


def test_run_saves_unverified_contacts_with_source_and_department(db, pages):
    pages(
        "https://t.example/water",
        """
        <html><head><title>Water Supply Cell</title></head><body>
        <a href="tel:29990001">Helpline</a>
        <a href="mailto:Water.Cell@Example.org">mail</a>
        </body></html>""",
    )

    stats, dropped = run_clean(db)

    rows = saved_contacts(db, ["https://t.example/water"])
    assert {(r.type, r.value) for r in rows} == {
        (ContactType.HELPLINE, "+912229990001"),
        (ContactType.EMAIL, "water.cell@example.org"),
    }
    assert all(r.verification_status == VerificationStatus.UNVERIFIED for r in rows)
    assert all(r.last_verified == date(2026, 11, 7) for r in rows)
    assert all(r.label for r in rows)
    authority = db.get(Authority, rows[0].authority_id)
    assert authority.name == AUTHORITY_NAME
    assert db.get(Department, authority.department_id).name == "Water Supply"
    assert stats["saved"] == 2 and not dropped


def test_second_run_adds_nothing(db, pages):
    pages(
        "https://t.example/once",
        """
        <html><head><title>Notices</title></head><body>
        <a href="tel:29990002">Helpline</a></body></html>""",
    )

    first, _ = run_clean(db)
    second, _ = run_clean(db)

    assert first["saved"] == 1
    assert second["saved"] == 0 and second["already_stored"] == 1
    assert len(saved_contacts(db, ["https://t.example/once"])) == 1


def test_same_contact_on_two_pages_is_kept_once(db, pages):
    body = (
        "<html><head><title>Notices</title></head><body>"
        '<a href="tel:29990003">Helpline</a></body></html>'
    )
    pages("https://t.example/a", body)
    pages("https://t.example/b", body)

    stats, dropped = run_clean(db)

    assert stats["found"] == 2 and stats["kept"] == 1
    assert dropped["duplicate"] == 1
    assert len(saved_contacts(db, ["https://t.example/a", "https://t.example/b"])) == 1


def test_dropped_values_are_counted_by_reason(db, pages):
    pages(
        "https://t.example/bad",
        """
        <html><head><title>Notices</title></head><body>
        <a href="tel:12345678901234">too long</a>
        <a href="mailto:nobody">broken</a>
        </body></html>""",
    )

    stats, dropped = run_clean(db)

    assert stats["found"] == 2 and stats["kept"] == 0
    assert dropped["wrong length"] == 1
    assert dropped["invalid email"] == 1
    assert saved_contacts(db, ["https://t.example/bad"]) == []


def test_a_page_that_cannot_be_parsed_is_skipped(db, pages, monkeypatch, capsys):
    pages("https://t.example/broken", "<html></html>")
    pages(
        "https://t.example/fine",
        """
        <html><head><title>Notices</title></head><body>
        <a href="tel:29990004">Helpline</a></body></html>""",
    )
    real_extract = clean_contacts.extract

    def flaky(html):
        if html == "<html></html>":
            raise ValueError("bad markup")
        return real_extract(html)

    monkeypatch.setattr(clean_contacts, "extract", flaky)

    stats, _ = run_clean(db)

    assert stats["pages_failed"] == 1 and stats["saved"] == 1
    assert "could not parse https://t.example/broken" in capsys.readouterr().out
