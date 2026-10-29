from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.models import Issue
from app.models.enums import IssueStatus

OPEN = (
    IssueStatus.NEW,
    IssueStatus.UNDER_REVIEW,
    IssueStatus.CLASSIFIED,
    IssueStatus.ASSIGNED,
    IssueStatus.ESCALATED,
    IssueStatus.REOPENED,
)
RESOLVED = (IssueStatus.RESOLVED, IssueStatus.VERIFIED, IssueStatus.CLOSED)
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
