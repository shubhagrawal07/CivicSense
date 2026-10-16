from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Issue, StatusHistory
from app.models.enums import IssueStatus


class IssueNotFound(Exception):
    pass


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
