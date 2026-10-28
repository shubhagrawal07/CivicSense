from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.stats import SummaryOut
from app.services.stats import summary_stats

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary", response_model=SummaryOut)
def summary(db: Annotated[Session, Depends(get_db)]):
    return summary_stats(db)
