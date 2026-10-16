from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.db import get_db
from app.models import User
from app.models.enums import UserRole
from app.schemas.admin import IssueStatusOut, StatusUpdateIn
from app.services.issues import IssueNotFound, change_status, parse_status

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.patch("/issues/{issue_id}/status", response_model=IssueStatusOut)
def update_issue_status(
    issue_id: int,
    body: StatusUpdateIn,
    admin: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
):
    new_status = parse_status(body.status)
    if new_status is None:
        raise HTTPException(status_code=400, detail="Unknown status")

    try:
        issue, entry = change_status(db, issue_id, new_status, body.note, admin.id)
    except IssueNotFound:
        raise HTTPException(status_code=404, detail="Issue not found") from None
    return IssueStatusOut(id=issue.id, status=issue.status, updated_at=entry.created_at)
