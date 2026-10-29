from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.stats import BreakdownOut, SummaryOut
from app.services.stats import breakdown_stats, summary_stats

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
