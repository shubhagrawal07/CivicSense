import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Issue, IssueReport, Report
from app.models.enums import IssueStatus

METHOD_NEW = "new_issue"
METHOD_GEO = "geo_category_v1"

CLOSED_STATUSES = (
    IssueStatus.RESOLVED,
    IssueStatus.VERIFIED,
    IssueStatus.CLOSED,
    IssueStatus.DUPLICATE,
    IssueStatus.REJECTED,
)

METRES_PER_DEGREE = 111_320


class MissingCategory(Exception):
    pass


@dataclass
class LinkResult:
    issue: Issue
    is_new: bool
    match_score: float
    method: str


def link_or_create_issue(db: Session, report: Report) -> LinkResult:
    if not report.classification:
        raise MissingCategory(report.id)

    lng, lat = db.execute(
        select(func.ST_X(Report.location), func.ST_Y(Report.location)).where(
            Report.id == report.id
        )
    ).one()
    now = datetime.now(timezone.utc)

    found = nearest_open_issue(db, report.classification, lat, lng, now)
    if found is None:
        issue = Issue(
            category=report.classification,
            location=func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
            severity=report.predicted_severity,
            status=IssueStatus.NEW,
            department_id=report.predicted_department_id,
            report_count=1,
            first_reported_at=now,
            last_reported_at=now,
        )
        db.add(issue)
        db.flush()
        score, method = 1.0, METHOD_NEW
    else:
        issue, distance_m = found
        score = match_score(distance_m, now - issue.last_reported_at)
        method = METHOD_GEO
        issue.report_count += 1
        issue.last_reported_at = now

    db.add(
        IssueReport(
            issue_id=issue.id,
            report_id=report.id,
            match_score=score,
            matching_method=method,
        )
    )
    db.flush()
    return LinkResult(issue, found is None, score, method)


def nearest_open_issue(db, category, lat, lng, now):
    radius = settings.link_radius_m
    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    pad = radius / (METRES_PER_DEGREE * max(math.cos(math.radians(lat)), 0.01))
    distance = func.ST_Distance(cast(Issue.location, Geography), cast(point, Geography))
    oldest = now - timedelta(days=settings.link_window_days)

    stmt = (
        select(Issue, distance)
        .where(Issue.location.op("&&")(func.ST_Expand(point, pad)))
        .where(
            func.ST_DWithin(
                cast(Issue.location, Geography), cast(point, Geography), radius
            )
        )
        .where(Issue.category == category)
        .where(Issue.status.not_in(CLOSED_STATUSES))
        .where(Issue.last_reported_at >= oldest)
        .order_by(distance, Issue.id)
        .limit(1)
    )
    row = db.execute(stmt).first()
    return (row[0], row[1]) if row else None


def match_score(distance_m: float, age: timedelta) -> float:
    s = settings
    geo = 1 - min(distance_m / s.link_radius_m, 1)
    recency = 1 - min(age / timedelta(days=s.link_window_days), 1)
    total = s.link_weight_geo + s.link_weight_category + s.link_weight_recency
    weighted = (
        s.link_weight_geo * geo
        + s.link_weight_category
        + s.link_weight_recency * recency
    )
    return round(weighted / total, 4)
