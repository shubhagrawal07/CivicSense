from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.enums import Severity
from app.schemas.map import MapFeatureCollection
from app.services.issues import map_issues

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get("/issues", response_model=MapFeatureCollection)
def issues(
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
    return map_issues(db, category, severity, status, start, end)
