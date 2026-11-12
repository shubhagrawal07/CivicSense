from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.enums import Severity
from app.schemas.issue import IssueOut
from app.services.issues import IssueNotFound, build_issue_out, export_issues_csv

router = APIRouter(prefix="/api/issues", tags=["issues"])


@router.get("/export.csv")
def export_csv(
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[str | None, Query()] = None,
    severity: Annotated[list[Severity] | None, Query()] = None,
    status: Annotated[
        list[Literal["open", "in_progress", "resolved"]] | None, Query()
    ] = None,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
):
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="'from' is after 'to'")
    csv_text = export_issues_csv(db, category, severity, status, start, end)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=issues.csv"},
    )


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return build_issue_out(db, issue_id)
    except IssueNotFound:
        raise HTTPException(status_code=404, detail="Issue not found") from None
