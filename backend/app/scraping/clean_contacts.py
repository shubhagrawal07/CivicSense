import re
import sys
from collections import Counter
from dataclasses import dataclass
from urllib.parse import urldefrag

from bs4 import BeautifulSoup
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.models import Authority, AuthorityContact, Department, RawDocument
from app.models.enums import ContactType, VerificationStatus

AUTHORITY_NAME = "Mumbai Police (scraped contacts)"
JURISDICTION = "Mumbai"
FALLBACK_DEPARTMENT = "General Grievance"
MUMBAI_STD_CODE = "22"
EMERGENCY_NUMBERS = {"100", "101", "102", "108", "112"}

# checked in this order, so a drainage page that also says "water" stays drainage
DEPARTMENT_PATTERNS = [
    ("Drainage / Sewerage", r"\b(?:drain|sewer|sewage|nullah|manhole)"),
    ("Water Supply", r"\bwater"),
    ("Roads / Public Works", r"\b(?:road|pothole|footpath|bridge)"),
    ("Sanitation / Solid Waste", r"\b(?:garbage|waste|sanitation|cleanliness)"),
    ("Electricity", r"\b(?:electric|power|street ?light)"),
]

PORTAL_WORDS = re.compile(r"complain|grievance|lodge", re.I)
# the everyday shape of an address, not the whole RFC grammar
EMAIL_SHAPE = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+$")
OBFUSCATED = [
    (re.compile(r"\s*[\[(]\s*at\s*[\])]\s*"), "@"),
    (re.compile(r"\s*[\[(]\s*dot\s*[\])]\s*"), "."),
    (re.compile(r"\s*[\[(]\s*dash\s*[\])]\s*"), "-"),
]
INVISIBLE = re.compile("[\u200b-\u200f\u2060\ufeff]")
PHONE_PREFIXES = {"+91", "91", "0", "022", "(022)", "+9122"}


@dataclass
class Found:
    kind: str  # phone, email or portal
    raw: str
    label: str
    context: str
    skip: str | None = None


def squash(text):
    return re.sub(r"\s+", " ", text).strip()


def clean_phone(raw):
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None, "no digits"
    if len(digits) > 4 and len(set(digits)) == 1:
        return None, "repeated digits"

    if digits[:4] in ("1800", "1860") and len(digits) in (10, 11):
        return digits, None
    if len(digits) in (3, 4) and digits[0] == "1":
        return digits, None

    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    if len(digits) == 8 and digits[0] in "23456789":
        return "+91" + MUMBAI_STD_CODE + digits, None
    if len(digits) == 10:
        if digits[0] in "23456789":
            return "+91" + digits, None
        return None, "unrecognised number"
    return None, "wrong length"


def split_emails(raw):
    text = INVISIBLE.sub("", raw).strip().lower()
    if text.startswith("mailto:"):
        text = text[7:]
    text = text.split("?")[0]
    for pattern, replacement in OBFUSCATED:
        text = pattern.sub(replacement, text)
    return [token for token in re.split(r"[\s/,;]+", text) if "@" in token]


def email_items(href, label, context):
    addresses = split_emails(href) or [href.split(":", 1)[-1]]
    return [Found("email", address, label, context) for address in addresses]


def clean_email(raw):
    text = INVISIBLE.sub("", raw).strip().lower()
    if EMAIL_SHAPE.match(text) and len(text) <= 254:
        return text, None
    return None, "invalid email"


def clean_portal(raw):
    url = urldefrag(raw.strip())[0]
    if not url.lower().startswith(("http://", "https://")):
        return None, "not a web link"
    if len(url) > 500:
        return None, "link too long"
    return url, None


def phone_type(value):
    return ContactType.EMERGENCY if value in EMERGENCY_NUMBERS else ContactType.HELPLINE


def pick_department(context):
    for name, pattern in DEPARTMENT_PATTERNS:
        if re.search(pattern, context, re.I):
            return name
    return FALLBACK_DEPARTMENT


def split_numbers(text):
    tokens = text.split()
    numbers = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in PHONE_PREFIXES and i + 1 < len(tokens):
            token = token + tokens[i + 1]
            i += 1
        if re.search(r"\d", token):
            numbers.append(token)
        i += 1
    return numbers


def heading_before(tag):
    heading = tag.find_previous(["h1", "h2", "h3"])
    return heading.get_text(" ", strip=True) if heading else ""


def from_tables(soup, title):
    found = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        head = [squash(c.get_text(" ")).lower() for c in rows[0].find_all(["td", "th"])]
        phone_cols = [i for i, h in enumerate(head) if "tel" in h or "phone" in h]
        fax_cols = [i for i, h in enumerate(head) if "fax" in h]
        if not phone_cols:
            continue

        context = title + " " + heading_before(table)
        for row in rows[1:]:
            cells = [squash(c.get_text(" ")) for c in row.find_all(["td", "th"])]
            if len(cells) <= max(phone_cols):
                continue
            label = cells[0]
            for col in phone_cols:
                for number in split_numbers(cells[col]):
                    found.append(Found("phone", number, label, context))
            for col in fax_cols:
                if col < len(cells):
                    for number in split_numbers(cells[col]):
                        found.append(
                            Found("phone", number, label, context, "fax number")
                        )
    return found


def card_label(card):
    top = card.select_one(".card-up")
    if top is None:
        return ""
    # the person's name is left out on purpose, only the post and area are kept
    heading = top.find("h4")
    name = heading.get_text(" ", strip=True) if heading else None
    parts = [squash(text) for text in top.stripped_strings if text != name]
    return re.sub(r"\(\s*(.*?)\s*\)", r"(\1)", " ".join(parts))


def from_cards(soup, title):
    found = []
    for card in soup.select("div.card-wrapper-sr"):
        label = card_label(card)
        context = title + " " + heading_before(card)
        for block in card.select(".card-down .marg-10"):
            icon = block.find("img")
            icon_name = icon.get("src", "").lower() if icon else ""
            for a in block.find_all("a", href=True):
                href = a["href"]
                if href.startswith("mailto:"):
                    found += email_items(href, label, context)
                elif href.startswith("tel:") and href[4:].strip():
                    number = href[4:].strip()
                    skip = None
                    if "fax" in icon_name:
                        skip = "fax number"
                    elif "mob" in icon_name:
                        skip = "officer mobile"
                    found.append(Found("phone", number, label, context, skip))
    return found


def link_label(a, title):
    own = a.get_text(" ", strip=True)
    around = a.parent.get_text(" ", strip=True) if a.parent else ""
    label = squash(around.replace(own, "")).strip(" :-|")
    # a long remainder means the parent is a whole section, not a caption
    if label and len(label) <= 80:
        return label
    return title.split("|")[0].strip()


def from_links(soup, title):
    found = []
    for a in soup.find_all("a", href=True):
        if a.find_parent("table") or a.find_parent(class_="card-wrapper-sr"):
            continue
        href = a["href"].strip()
        context = title + " " + heading_before(a)
        if href.startswith("tel:") and href[4:].strip():
            found.append(Found("phone", href[4:], link_label(a, title), context))
        elif href.startswith("mailto:"):
            found += email_items(href, link_label(a, title), context)
        elif href.startswith(("http://", "https://")):
            text = a.get_text(" ", strip=True)
            if PORTAL_WORDS.search(text + " " + href):
                found.append(Found("portal", href, text or "Complaint portal", context))
    return found


def extract(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    return from_tables(soup, title) + from_cards(soup, title) + from_links(soup, title)


def clean_item(item):
    if item.skip:
        return None, None, item.skip
    if item.kind == "phone":
        value, reason = clean_phone(item.raw)
        return value, value and phone_type(value), reason
    if item.kind == "email":
        value, reason = clean_email(item.raw)
        return value, ContactType.EMAIL, reason
    value, reason = clean_portal(item.raw)
    return value, ContactType.COMPLAINT_PORTAL, reason


def latest_documents(db):
    newest = select(func.max(RawDocument.id)).group_by(RawDocument.source_url)
    stmt = (
        select(RawDocument).where(RawDocument.id.in_(newest)).order_by(RawDocument.id)
    )
    return db.scalars(stmt).all()


def authority_for(db, department):
    authority = db.scalar(
        select(Authority).where(
            Authority.name == AUTHORITY_NAME,
            Authority.department_id == department.id,
        )
    )
    if authority is None:
        authority = Authority(
            name=AUTHORITY_NAME,
            jurisdiction=JURISDICTION,
            department_id=department.id,
        )
        db.add(authority)
        db.flush()
    return authority


def run_clean(db):
    departments = {d.name: d for d in db.scalars(select(Department))}
    stats = Counter()
    dropped = Counter()
    seen = set()

    for doc in latest_documents(db):
        try:
            items = extract(doc.content)
        except Exception as error:
            print(f"could not parse {doc.source_url} ({error})")
            stats["pages_failed"] += 1
            continue
        if not items:
            print(f"nothing found on {doc.source_url}")

        for item in items:
            stats["found"] += 1
            value, kind, reason = clean_item(item)
            if reason:
                dropped[reason] += 1
                continue
            if (kind, value) in seen:
                dropped["duplicate"] += 1
                continue
            seen.add((kind, value))
            stats["kept"] += 1

            department = departments.get(pick_department(item.context))
            if department is None:
                department = departments[FALLBACK_DEPARTMENT]
            authority = authority_for(db, department)
            exists = db.scalar(
                select(AuthorityContact.id).where(
                    AuthorityContact.authority_id == authority.id,
                    AuthorityContact.type == kind,
                    AuthorityContact.value == value,
                )
            )
            if exists is not None:
                stats["already_stored"] += 1
                continue
            db.add(
                AuthorityContact(
                    authority_id=authority.id,
                    type=kind,
                    value=value,
                    label=item.label[:300] or None,
                    source_url=doc.source_url,
                    last_verified=doc.fetched_at.date(),
                    verification_status=VerificationStatus.UNVERIFIED,
                )
            )
            stats["saved"] += 1

    db.commit()
    return stats, dropped


def print_summary(stats, dropped):
    print(
        f"found {stats['found']}, kept {stats['kept']}, dropped {sum(dropped.values())}"
    )
    print(f"kept: {stats['saved']} saved, {stats['already_stored']} already stored")
    for reason, count in dropped.most_common():
        print(f"dropped {count}: {reason}")
    if stats["pages_failed"]:
        print(f"pages that could not be parsed: {stats['pages_failed']}")


def main():
    db = SessionLocal()
    try:
        if not latest_documents(db):
            print("no stored pages, run app.scraping.fetch_contacts first")
            sys.exit(1)
        stats, dropped = run_clean(db)
        print_summary(stats, dropped)
    finally:
        db.close()


if __name__ == "__main__":
    main()
