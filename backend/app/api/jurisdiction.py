from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.enums import JurisdictionStatus
from app.schemas.jurisdiction import JurisdictionAtOut
from app.services.jurisdiction import jurisdictions_at, list_jurisdictions

router = APIRouter(prefix="/api/jurisdictions", tags=["jurisdictions"])


@router.get("")
def jurisdiction_boundaries(
    db: Annotated[Session, Depends(get_db)],
    type: str | None = None,
    status: JurisdictionStatus = JurisdictionStatus.APPROVED,
):
    return list_jurisdictions(db, type, status)


@router.get("/at", response_model=list[JurisdictionAtOut])
def jurisdictions_at_point(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    db: Annotated[Session, Depends(get_db)],
):
    return jurisdictions_at(db, lat, lng)
