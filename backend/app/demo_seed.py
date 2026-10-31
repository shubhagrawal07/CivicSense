import argparse
import random
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import delete, func, select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import Issue, IssueReport, Report, ReportImage, StatusHistory, User
from app.models.enums import ProcessingStatus, UserRole
from app.seed import seed_admin, seed_authorities, seed_departments
from app.seed_data.demo_reports import (
    CITIZENS,
    DEMO_DOMAIN,
    DEMO_PASSWORD,
    FAILED_REPORT,
    REPORTS,
    STATUS_PLAN,
)
from app.services.auth import normalize_email
from app.services.issues import change_status
from app.services.reports import create_report
from app.workers.pipeline import process_report

EMAIL_PREFIX = "demo."
IMAGE_PREFIX = "demo_"
FALLBACK_ADMIN = f"{EMAIL_PREFIX}admin@{DEMO_DOMAIN}"
PROCESSING_DELAY = timedelta(seconds=25)

BACKGROUNDS = {
    "pothole": (92, 92, 98),
    "open_manhole": (70, 78, 84),
    "garbage": (96, 110, 80),
    "streetlight": (28, 34, 58),
    "water_leakage": (70, 110, 140),
    "electricity_outage": (60, 54, 70),
    "drainage_sewage": (86, 94, 70),
    "damaged_infrastructure": (120, 108, 96),
    "road_obstruction": (84, 104, 76),
}

NOTES = {
    "UNDER_REVIEW": "Picked up for review",
    "ASSIGNED": "Assigned to the ward office",
    "IN_PROGRESS": "Crew sent to the spot",
    "RESOLVED": "Work completed, waiting for confirmation",
    "ESCALATED": "No action after 48 hours, escalated to the ward officer",
    "REJECTED": "Could not find the problem at this location",
    "CLOSED": "Confirmed fixed by a nearby resident",
}


def demo_email(key):
    return f"{EMAIL_PREFIX}{key}@{DEMO_DOMAIN}"


def draw_photo(category, number):
    rng = random.Random(number)
    base = BACKGROUNDS[category]
    image = Image.new("RGB", (640, 480), base)
    draw = ImageDraw.Draw(image)
    for _ in range(14):
        x, y = rng.randint(0, 600), rng.randint(0, 440)
        shade = rng.randint(-25, 25)
        colour = tuple(max(0, min(255, c + shade)) for c in base)
        draw.ellipse(
            (x, y, x + rng.randint(30, 140), y + rng.randint(20, 90)), fill=colour
        )
    draw.rectangle((0, 400, 640, 480), fill=(24, 24, 24))
    font = ImageFont.load_default(size=26)
    draw.text(
        (20, 420),
        f"sample photo: {category.replace('_', ' ')}",
        fill="white",
        font=font,
    )
    return image


def save_photo(category, number):
    name = f"{IMAGE_PREFIX}{number:02d}.jpg"
    draw_photo(category, number).save(settings.upload_path / name, quality=80)
    return name


def make_citizens(db):
    users = {}
    for key, name in CITIZENS:
        user = User(
            name=name,
            email=demo_email(key),
            password_hash=hash_password(DEMO_PASSWORD),
            role=UserRole.CITIZEN,
        )
        db.add(user)
        users[key] = user
    db.commit()
    return users


def get_admin(db):
    email = settings.admin_email or FALLBACK_ADMIN
    password = settings.admin_password or DEMO_PASSWORD
    if seed_admin(db, "Demo Admin", email, password):
        print(f"created admin {normalize_email(email)}")
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def backdate(db, report, days_ago, now):
    created = now - timedelta(days=days_ago)
    report.created_at = created
    if report.processed_at is not None:
        report.processed_at = created + PROCESSING_DELAY
    link = db.scalar(select(IssueReport).where(IssueReport.report_id == report.id))
    if link is not None:
        link.linked_at = created + PROCESSING_DELAY


def fix_issue_times(db, issue_ids):
    for issue_id in issue_ids:
        first, last = db.execute(
            select(func.min(Report.created_at), func.max(Report.created_at))
            .join(IssueReport, IssueReport.report_id == Report.id)
            .where(IssueReport.issue_id == issue_id)
        ).one()
        issue = db.get(Issue, issue_id)
        issue.first_reported_at = first
        issue.last_reported_at = last
        created_entry = db.scalar(
            select(StatusHistory).where(
                StatusHistory.issue_id == issue_id, StatusHistory.old_status.is_(None)
            )
        )
        if created_entry is not None:
            created_entry.created_at = first + PROCESSING_DELAY


def apply_statuses(db, admin, issue_by_tag, now):
    for tag, path in STATUS_PLAN.items():
        issue = db.get(Issue, issue_by_tag[tag])
        step = max(
            (now - issue.first_reported_at) / (len(path) + 1), timedelta(hours=1)
        )
        for number, status in enumerate(path, start=1):
            _, entry = change_status(
                db, issue.id, status, NOTES.get(status.value), admin.id
            )
            entry.created_at = min(issue.first_reported_at + step * number, now)
            if status.value == "RESOLVED":
                issue.resolved_at = entry.created_at
        db.commit()


def add_failed_report(db, users, now):
    key, text, lat, lng, error, days_ago = FAILED_REPORT
    report = create_report(db, users[key].id, text, None, lat, lng)
    report.processing_status = ProcessingStatus.FAILED
    report.error = error
    report.created_at = now - timedelta(days=days_ago)
    report.processed_at = report.created_at + PROCESSING_DELAY
    db.commit()


def demo_loaded(db):
    return db.scalar(select(User.id).where(User.email == demo_email(CITIZENS[0][0])))


def load(db):
    if demo_loaded(db):
        raise SystemExit("demo data is already loaded, run with --reset first")

    seed_departments(db)
    seed_authorities(db)
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    users = make_citizens(db)
    admin = get_admin(db)
    now = datetime.now(timezone.utc)

    # oldest first, so later reports find the issues earlier ones opened
    ordered = sorted(enumerate(REPORTS), key=lambda pair: -pair[1][5])
    made = []
    for number, (who, text, lat, lng, photo, days_ago, expected, tag) in ordered:
        image_name = save_photo(photo, number) if photo else None
        report = create_report(db, users[who].id, text, image_name, lat, lng)
        process_report(report.id, db)
        db.refresh(report)
        made.append((report, days_ago, expected, tag))

    issue_by_tag = {}
    issue_ids = set()
    for report, days_ago, expected, tag in made:
        if report.processing_status != ProcessingStatus.DONE:
            status = report.processing_status.value
            print(f"report {report.id} ended {status}: {report.error}")
        elif report.classification != expected:
            got = report.classification
            print(f"report {report.id} classified as {got}, expected {expected}")
        backdate(db, report, days_ago, now)
        link = db.scalar(select(IssueReport).where(IssueReport.report_id == report.id))
        if link is not None:
            issue_ids.add(link.issue_id)
            if tag:
                issue_by_tag[tag] = link.issue_id
    db.commit()

    fix_issue_times(db, issue_ids)
    db.commit()
    apply_statuses(db, admin, issue_by_tag, now)
    add_failed_report(db, users, now)

    print(f"loaded {len(REPORTS) + 1} reports into {len(issue_ids)} issues")
    print(f"citizen password is {DEMO_PASSWORD}, e.g. {demo_email(CITIZENS[0][0])}")


def remove_users(db, user_ids):
    """Delete the users, their reports, and issues left with no reports."""
    report_ids = db.scalars(select(Report.id).where(Report.user_id.in_(user_ids))).all()
    photos = db.scalars(
        select(ReportImage.file_name).where(ReportImage.report_id.in_(report_ids))
    ).all()
    issue_ids = db.scalars(
        select(IssueReport.issue_id).where(IssueReport.report_id.in_(report_ids))
    ).all()

    db.execute(delete(IssueReport).where(IssueReport.report_id.in_(report_ids)))
    orphans = [
        i
        for i in set(issue_ids)
        if not db.scalar(select(IssueReport.id).where(IssueReport.issue_id == i))
    ]
    db.execute(delete(StatusHistory).where(StatusHistory.issue_id.in_(orphans)))
    db.execute(delete(Issue).where(Issue.id.in_(orphans)))
    db.execute(delete(Report).where(Report.id.in_(report_ids)))
    db.execute(delete(User).where(User.id.in_(user_ids)))
    db.commit()

    for name in photos:
        (settings.upload_path / name).unlink(missing_ok=True)
    return len(report_ids), len(orphans), len(user_ids)


def reset(db):
    admin_email = normalize_email(settings.admin_email or FALLBACK_ADMIN)
    user_ids = db.scalars(
        select(User.id).where(
            User.email.like(f"{EMAIL_PREFIX}%@{DEMO_DOMAIN}"), User.email != admin_email
        )
    ).all()
    counts = remove_users(db, user_ids)
    print("removed %d reports, %d issues, %d users" % counts)


def main():
    parser = argparse.ArgumentParser(description="Load or remove the demo data")
    parser.add_argument("--reset", action="store_true", help="remove the demo data")
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.reset:
            reset(db)
        else:
            load(db)


if __name__ == "__main__":
    main()
