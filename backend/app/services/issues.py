from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Department, Issue, StatusHistory
from app.models.enums import IssueStatus
from app.schemas.issue import IssueOut, StatusHistoryOut
from app.schemas.report import LatLng
from app.services.authority import contacts_out, lookup_authority


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
