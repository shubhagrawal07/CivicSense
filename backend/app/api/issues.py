from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.issue import IssueOut
from app.services.issues import IssueNotFound, build_issue_out

router = APIRouter(prefix="/api/issues", tags=["issues"])


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return build_issue_out(db, issue_id)
    except IssueNotFound:
        raise HTTPException(status_code=404, detail="Issue not found") from None
