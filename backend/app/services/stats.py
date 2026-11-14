from datetime import date

from sqlalchemy import Date, and_, cast, extract, func, select
from sqlalchemy.orm import Session

from app.models import Issue, Jurisdiction
from app.models.enums import IssueStatus, Severity

OPEN = (
    IssueStatus.NEW,
    IssueStatus.UNDER_REVIEW,
    IssueStatus.CLASSIFIED,
    IssueStatus.ASSIGNED,
    IssueStatus.ESCALATED,
    IssueStatus.REOPENED,
)
RESOLVED = (IssueStatus.RESOLVED, IssueStatus.VERIFIED, IssueStatus.CLOSED)
HIGH_SEVERITIES = (Severity.HIGH, Severity.CRITICAL)
BUCKETS = {
    "open": OPEN,
    "in_progress": (IssueStatus.IN_PROGRESS,),
    "resolved": RESOLVED,
}


def summary_stats(db: Session) -> dict:
    seconds_to_resolve = extract("epoch", Issue.resolved_at - Issue.first_reported_at)
    row = db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Issue.status.in_(OPEN)).label("open"),
            func.count()
            .filter(Issue.status == IssueStatus.IN_PROGRESS)
            .label("in_progress"),
            func.count().filter(Issue.status.in_(RESOLVED)).label("resolved"),
            func.avg(seconds_to_resolve)
            .filter(Issue.status.in_(RESOLVED), Issue.resolved_at.is_not(None))
            .label("avg_seconds"),
        )
    ).one()

    avg_days = None
    if row.avg_seconds is not None:
        avg_days = round(float(row.avg_seconds) / 86400, 1)

    return {
        "total": row.total,
        "open": row.open,
        "in_progress": row.in_progress,
        "resolved": row.resolved,
        "avg_resolution_days": avg_days,
    }


def breakdown_stats(db: Session, status: str | None = None) -> dict:
    def count_by(column):
        n = func.count().label("count")
        query = (
            select(column, n)
            .where(column.is_not(None))
            .group_by(column)
            .order_by(n.desc(), column)
        )
        if status:
            query = query.where(Issue.status.in_(BUCKETS[status]))
        return db.execute(query).all()

    return {
        "by_category": [
            {"category": r.category, "count": r.count} for r in count_by(Issue.category)
        ],
        "by_severity": [
            {"severity": r.severity, "count": r.count} for r in count_by(Issue.severity)
        ],
    }


def trend_stats(
    db: Session,
    interval: str = "week",
    category: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> list[dict]:
    reported_utc = func.timezone("UTC", Issue.first_reported_at)
    period = cast(func.date_trunc(interval, reported_utc), Date).label("period")
    query = (
        select(period, func.count().label("count")).group_by(period).order_by(period)
    )

    if category:
        query = query.where(Issue.category == category)
    if start:
        query = query.where(cast(reported_utc, Date) >= start)
    if end:
        query = query.where(cast(reported_utc, Date) <= end)

    return [{"period": r.period, "count": r.count} for r in db.execute(query)]


def by_ward_stats(
    db: Session,
    category: str | None = None,
    severity: Severity | None = None,
    start: date | None = None,
    end: date | None = None,
) -> list[dict]:
    join_conditions = [func.ST_Contains(Jurisdiction.boundary, Issue.location)]
    reported_utc = func.timezone("UTC", Issue.first_reported_at)
    if category:
        join_conditions.append(Issue.category == category)
    if severity:
        join_conditions.append(Issue.severity == severity)
    if start:
        join_conditions.append(cast(reported_utc, Date) >= start)
    if end:
        join_conditions.append(cast(reported_utc, Date) <= end)

    query = (
        select(
            Jurisdiction.id,
            Jurisdiction.name,
            func.count(Issue.id).label("issue_count"),
            func.count(Issue.id).filter(Issue.status.in_(OPEN)).label("open_count"),
            func.count(Issue.id)
            .filter(Issue.severity.in_(HIGH_SEVERITIES))
            .label("high_severity_count"),
        )
        .select_from(Jurisdiction)
        .outerjoin(Issue, and_(*join_conditions))
        .where(Jurisdiction.type == "ward")
        .group_by(Jurisdiction.id, Jurisdiction.name)
        .order_by(Jurisdiction.name)
    )

    return [
        {
            "ward_id": r.id,
            "ward_name": r.name,
            "issue_count": r.issue_count,
            "open_count": r.open_count,
            "high_severity_count": r.high_severity_count,
        }
        for r in db.execute(query)
    ]
