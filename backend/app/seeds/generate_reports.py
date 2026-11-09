import argparse
import random
from datetime import datetime, timedelta, timezone

from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy import delete, func, select

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.intelligence.departments import department_for
from app.intelligence.severity import CATEGORY_DEFAULTS, LEVELS, POINTS_PER_LEVEL
from app.models import Issue, IssueReport, Jurisdiction, Report, StatusHistory, User
from app.models.enums import (
    ClassificationSource,
    IssueStatus,
    JurisdictionStatus,
    ProcessingStatus,
)
from app.services.auth import normalize_email
from app.workers.pipeline import stage_authority, stage_link

SYNTHETIC_EMAIL = "synthetic.citizen@example.com"
SYNTHETIC_NAME = "Synthetic Citizen"
SYNTHETIC_PASSWORD = "synthetic-data"

MIN_LNG, MAX_LNG = 72.7, 73.1
MIN_LAT, MAX_LAT = 18.85, 19.35

METERS_PER_DEGREE = 111320
CLUSTER_JITTER_METERS = 15
REPORTS_PER_CLUSTER = 8

CATEGORY_WEIGHTS = {
    "pothole": 20,
    "garbage": 18,
    "drainage_sewage": 10,
    "road_obstruction": 10,
    "streetlight": 10,
    "damaged_infrastructure": 9,
    "water_leakage": 8,
    "open_manhole": 7,
    "electricity_outage": 5,
    "other": 3,
}

STATUS_WEIGHTS = {
    IssueStatus.NEW: 40,
    IssueStatus.IN_PROGRESS: 20,
    IssueStatus.RESOLVED: 40,
}

DESCRIPTIONS = {
    "pothole": [
        "Large pothole causing traffic to swerve.",
        "Deep pothole, risky for two-wheelers.",
    ],
    "garbage": [
        "Garbage pile not collected for days.",
        "Overflowing bin attracting flies and stray animals.",
    ],
    "open_manhole": [
        "Manhole cover missing, dangerous at night.",
        "Open manhole near the footpath, no barricade.",
    ],
    "streetlight": [
        "Streetlight not working for over a week.",
        "Pole here flickers all night.",
    ],
    "water_leakage": [
        "Pipe leaking continuously, water wasted on the road.",
        "Burst pipe flooding the lane.",
    ],
    "electricity_outage": [
        "Frequent power cuts in this area.",
        "Exposed wire hanging near the pole.",
    ],
    "drainage_sewage": [
        "Drain blocked, water stagnating.",
        "Sewage overflow, smell is bad.",
    ],
    "damaged_infrastructure": [
        "Footpath tiles broken and uneven.",
        "Railing damaged near the junction.",
    ],
    "road_obstruction": [
        "Fallen tree blocking half the road.",
        "Construction debris left on the road.",
    ],
    "other": [
        "Civic issue needs attention here.",
        "Problem reported by a resident.",
    ],
}


def weighted_choice(rng, weights):
    options = list(weights.keys())
    values = list(weights.values())
    return rng.choices(options, weights=values)[0]


def pick_category(rng):
    return weighted_choice(rng, CATEGORY_WEIGHTS)


def pick_status(rng):
    return weighted_choice(rng, STATUS_WEIGHTS)


def pick_description(rng, category):
    return rng.choice(DESCRIPTIONS[category])


def get_synthetic_user(db):
    email = normalize_email(SYNTHETIC_EMAIL)
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user
    user = User(
        name=SYNTHETIC_NAME,
        email=email,
        password_hash=hash_password(SYNTHETIC_PASSWORD),
    )
    db.add(user)
    db.commit()
    return user


def load_ward_polygons(db):
    rows = db.scalars(
        select(Jurisdiction.boundary).where(
            Jurisdiction.status == JurisdictionStatus.APPROVED
        )
    ).all()
    if not rows:
        rows = db.scalars(select(Jurisdiction.boundary)).all()
    return [to_shape(row) for row in rows]


def random_point_in_bbox(rng):
    lat = rng.uniform(MIN_LAT, MAX_LAT)
    lng = rng.uniform(MIN_LNG, MAX_LNG)
    return lat, lng


def random_point(rng, polygons):
    if not polygons:
        return random_point_in_bbox(rng)
    polygon = rng.choice(polygons)
    min_lng, min_lat, max_lng, max_lat = polygon.bounds
    for _ in range(10):
        lat = rng.uniform(min_lat, max_lat)
        lng = rng.uniform(min_lng, max_lng)
        if polygon.contains(Point(lng, lat)):
            return lat, lng
    return random_point_in_bbox(rng)


def jitter_point(rng, lat, lng, max_meters=CLUSTER_JITTER_METERS):
    offset_lat = rng.uniform(-max_meters, max_meters) / METERS_PER_DEGREE
    offset_lng = rng.uniform(-max_meters, max_meters) / METERS_PER_DEGREE
    return lat + offset_lat, lng + offset_lng


def build_clusters(rng, count, polygons):
    num_clusters = max(5, count // REPORTS_PER_CLUSTER)
    clusters = []
    for _ in range(num_clusters):
        lat, lng = random_point(rng, polygons)
        clusters.append({"category": pick_category(rng), "lat": lat, "lng": lng})
    return clusters


def build_plan(rng, count, polygons):
    clusters = build_clusters(rng, count, polygons)
    plan = []
    for _ in range(count):
        cluster = rng.choice(clusters)
        category = cluster["category"]
        lat, lng = jitter_point(rng, cluster["lat"], cluster["lng"])
        plan.append(
            {
                "category": category,
                "severity": CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS["other"]),
                "lat": lat,
                "lng": lng,
                "description": pick_description(rng, category),
                "days_ago": rng.uniform(0, 90),
            }
        )
    plan.sort(key=lambda item: -item["days_ago"])
    return plan


def make_report(db, user, item):
    department = department_for(db, item["category"], confidence=1.0)
    report = Report(
        user_id=user.id,
        description=item["description"],
        location=func.ST_SetSRID(func.ST_MakePoint(item["lng"], item["lat"]), 4326),
        processing_status=ProcessingStatus.PENDING,
        classification=item["category"],
        classification_confidence=1.0,
        classification_source=ClassificationSource.TEXT,
        predicted_department_id=department["department_id"],
        department_confidence=department["confidence"],
        predicted_severity=item["severity"],
        is_synthetic=True,
    )
    db.add(report)
    db.flush()
    return report


def severity_dict(level):
    score = (LEVELS.index(level) + 1) * POINTS_PER_LEVEL
    return {"level": level, "score": score, "reasons": ["synthetic data"]}


def run_pipeline_for(db, report):
    issue = stage_link(db, report, severity_dict(report.predicted_severity))
    issue.is_synthetic = True
    stage_authority(db, report, issue)
    report.processing_status = ProcessingStatus.DONE
    report.processed_at = datetime.now(timezone.utc)
    return issue


def backdate_report(db, report, days_ago, now):
    created = now - timedelta(days=days_ago)
    report.created_at = created
    report.processed_at = created
    link = db.scalar(select(IssueReport).where(IssueReport.report_id == report.id))
    if link is not None:
        link.linked_at = created


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
            created_entry.created_at = first


def apply_status(db, rng, issue, now):
    status = pick_status(rng)
    if status == IssueStatus.NEW:
        return
    old_status = issue.status
    issue.status = status
    if status == IssueStatus.RESOLVED:
        days = rng.uniform(3, 21)
        resolved_at = min(issue.first_reported_at + timedelta(days=days), now)
        issue.resolved_at = resolved_at
        entry_time = resolved_at
    else:
        entry_time = min(issue.first_reported_at + timedelta(days=1), now)
    db.add(
        StatusHistory(
            issue_id=issue.id,
            old_status=old_status,
            new_status=status,
            note="synthetic data",
            created_at=entry_time,
        )
    )


def load(db, count=1000, seed=None):
    rng = random.Random(seed)
    user = get_synthetic_user(db)
    polygons = load_ward_polygons(db)
    now = datetime.now(timezone.utc)

    plan = build_plan(rng, count, polygons)
    issue_ids = set()
    for item in plan:
        report = make_report(db, user, item)
        issue = run_pipeline_for(db, report)
        issue_ids.add(issue.id)
        backdate_report(db, report, item["days_ago"], now)
    db.commit()

    fix_issue_times(db, issue_ids)
    db.commit()

    for issue_id in issue_ids:
        issue = db.get(Issue, issue_id)
        apply_status(db, rng, issue, now)
    db.commit()

    print(f"created {len(plan)} synthetic reports across {len(issue_ids)} issues")


def reset(db):
    report_ids = db.scalars(select(Report.id).where(Report.is_synthetic)).all()
    issue_ids = db.scalars(select(Issue.id).where(Issue.is_synthetic)).all()

    db.execute(delete(IssueReport).where(IssueReport.report_id.in_(report_ids)))
    db.execute(delete(StatusHistory).where(StatusHistory.issue_id.in_(issue_ids)))
    db.execute(delete(Issue).where(Issue.id.in_(issue_ids)))
    db.execute(delete(Report).where(Report.id.in_(report_ids)))
    db.commit()

    print(f"removed {len(report_ids)} synthetic reports")
    print(f"removed {len(issue_ids)} synthetic issues")


def main():
    parser = argparse.ArgumentParser(description="Generate or remove synthetic reports")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.reset:
            reset(db)
        else:
            load(db, args.count, args.seed)


if __name__ == "__main__":
    main()
