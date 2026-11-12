import csv
import io
from datetime import date, datetime, timezone

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from app.models import Authority, Department, Issue, StatusHistory
from app.models.enums import IssueStatus, Severity
from app.schemas.issue import IssueOut, StatusHistoryOut
from app.schemas.report import LatLng
from app.services.authority import contacts_out, lookup_authority
from app.services.stats import BUCKETS

MAP_LIMIT = 2000
EXPORT_LIMIT = 5000


class IssueNotFound(Exception):
    pass


def build_issue_out(db: Session, issue_id: int) -> IssueOut:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise IssueNotFound()

    lng, lat = db.execute(
        select(func.ST_X(Issue.location), func.ST_Y(Issue.location)).where(
            Issue.id == issue.id
        )
    ).one()

    department = None
    authority = None
    contacts = []
    if issue.department_id:
        department = db.get(Department, issue.department_id)
        match = lookup_authority(db, issue.department_id, lat, lng)
        authority = match.authority
        contacts = contacts_out(match.contacts)

    rows = db.scalars(
        select(StatusHistory)
        .where(StatusHistory.issue_id == issue.id)
        .order_by(StatusHistory.created_at, StatusHistory.id)
    ).all()
    history = []
    for row in rows:
        history.append(
            StatusHistoryOut(
                status=row.new_status, changed_at=row.created_at, note=row.note
            )
        )

    return IssueOut(
        id=issue.id,
        category=issue.category,
        severity=issue.severity,
        status=issue.status,
        location=LatLng(lat=lat, lng=lng),
        report_count=issue.report_count,
        first_reported_at=issue.first_reported_at,
        last_reported_at=issue.last_reported_at,
        department=department,
        authority=authority,
        contacts=contacts,
        status_history=history,
    )


def parse_status(value: str) -> IssueStatus | None:
    try:
        return IssueStatus(value.strip().upper())
    except ValueError:
        return None


def change_status(
    db: Session, issue_id: int, new_status: IssueStatus, note: str | None, user_id: int
) -> tuple[Issue, StatusHistory]:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise IssueNotFound()

    entry = StatusHistory(
        issue_id=issue.id,
        old_status=issue.status,
        new_status=new_status,
        changed_by=user_id,
        note=note.strip() if note and note.strip() else None,
    )
    issue.status = new_status
    if new_status == IssueStatus.RESOLVED:
        issue.resolved_at = datetime.now(timezone.utc)

    db.add(entry)
    db.commit()
    db.refresh(entry)
    return issue, entry


def filter_issues(
    query,
    category: str | None = None,
    severities: list[Severity] | None = None,
    statuses: list[str] | None = None,
    start: date | None = None,
    end: date | None = None,
):
    if category:
        query = query.where(Issue.category == category)
    if severities:
        query = query.where(Issue.severity.in_(severities))
    if statuses:
        wanted = []
        for bucket in statuses:
            wanted.extend(BUCKETS[bucket])
        query = query.where(Issue.status.in_(wanted))

    reported_day = cast(func.timezone("UTC", Issue.last_reported_at), Date)
    if start:
        query = query.where(reported_day >= start)
    if end:
        query = query.where(reported_day <= end)
    return query


def map_issues(
    db: Session,
    category: str | None = None,
    severities: list[Severity] | None = None,
    statuses: list[str] | None = None,
    start: date | None = None,
    end: date | None = None,
) -> dict:
    query = select(
        Issue.id,
        Issue.category,
        Issue.severity,
        Issue.status,
        Issue.report_count,
        Issue.last_reported_at,
        func.ST_X(Issue.location).label("lng"),
        func.ST_Y(Issue.location).label("lat"),
    ).where(Issue.location.is_not(None))
    query = filter_issues(query, category, severities, statuses, start, end)
    query = query.order_by(Issue.last_reported_at.desc(), Issue.id.desc())
    query = query.limit(MAP_LIMIT)

    features = []
    for row in db.execute(query):
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row.lng, row.lat]},
                "properties": {
                    "id": row.id,
                    "category": row.category,
                    "severity": row.severity,
                    "status": row.status,
                    "report_count": row.report_count,
                    "last_reported_at": row.last_reported_at,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def export_issues_csv(
    db: Session,
    category: str | None = None,
    severities: list[Severity] | None = None,
    statuses: list[str] | None = None,
    start: date | None = None,
    end: date | None = None,
) -> str:
    query = (
        select(
            Issue.id,
            Issue.category,
            Issue.severity,
            Issue.status,
            Issue.report_count,
            Department.name.label("department"),
            Authority.name.label("authority"),
            func.ST_Y(Issue.location).label("lat"),
            func.ST_X(Issue.location).label("lng"),
            Issue.first_reported_at,
            Issue.last_reported_at,
            Issue.resolved_at,
            Issue.is_synthetic,
        )
        .outerjoin(Department, Issue.department_id == Department.id)
        .outerjoin(Authority, Issue.authority_id == Authority.id)
        .where(Issue.location.is_not(None))
    )
    query = filter_issues(query, category, severities, statuses, start, end)
    query = query.order_by(Issue.last_reported_at.desc(), Issue.id.desc())
    query = query.limit(EXPORT_LIMIT)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "category",
            "severity",
            "status",
            "report_count",
            "department",
            "authority",
            "latitude",
            "longitude",
            "first_reported_at",
            "last_reported_at",
            "resolved_at",
            "is_synthetic",
        ]
    )
    for row in db.execute(query):
        writer.writerow(
            [
                row.id,
                row.category,
                row.severity.value if row.severity else "",
                row.status.value,
                row.report_count,
                row.department or "",
                row.authority or "",
                row.lat,
                row.lng,
                row.first_reported_at,
                row.last_reported_at,
                row.resolved_at or "",
                row.is_synthetic,
            ]
        )
    return buffer.getvalue()
