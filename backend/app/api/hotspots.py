from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.hotspots import HotspotCell
from app.services.hotspots import hotspot_cells

router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])


@router.get("", response_model=list[HotspotCell])
def hotspots(
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[str | None, Query()] = None,
    days: Annotated[int, Query(ge=1)] = 90,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
):
    return hotspot_cells(db, category, days, limit)
