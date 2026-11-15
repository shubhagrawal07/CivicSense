from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.enums import Severity
from app.schemas.stats import BreakdownOut, SummaryOut, TrendPoint, WardCount
from app.services.stats import (
    breakdown_stats,
    by_ward_stats,
    summary_stats,
    trend_stats,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary", response_model=SummaryOut)
def summary(db: Annotated[Session, Depends(get_db)]):
    return summary_stats(db)


@router.get("/breakdown", response_model=BreakdownOut)
def breakdown(
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[
        Literal["open", "in_progress", "resolved"] | None, Query()
    ] = None,
):
    return breakdown_stats(db, status)


@router.get("/trend", response_model=list[TrendPoint])
def trend(
    db: Annotated[Session, Depends(get_db)],
    interval: Annotated[Literal["day", "week"], Query()] = "week",
    category: Annotated[str | None, Query()] = None,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
):
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="'from' is after 'to'")
    return trend_stats(db, interval, category, start, end)


@router.get("/by-ward", response_model=list[WardCount])
def by_ward(
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[str | None, Query()] = None,
    severity: Annotated[Severity | None, Query()] = None,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
):
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="'from' is after 'to'")
    return by_ward_stats(db, category, severity, start, end)
