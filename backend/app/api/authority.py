from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.authority import AuthorityInfoOut, ContactOut
from app.services.authority import DepartmentNotFound, lookup_authority

router = APIRouter(prefix="/api")


@router.get("/authority-info", response_model=AuthorityInfoOut)
def authority_info(
    department_id: int,
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        match = lookup_authority(db, department_id, lat, lng)
    except DepartmentNotFound:
        raise HTTPException(status_code=404, detail="Unknown department") from None

    return AuthorityInfoOut(
        department=match.department,
        authority=match.authority,
        contacts=[
            ContactOut(
                type=c.type,
                value=c.value,
                source_url=c.source_url,
                last_verified_at=c.last_verified,
                verified=c.verified,
            )
            for c in match.contacts
        ],
        is_fallback=match.is_fallback,
        needs_review=match.needs_review,
        other_matches=match.other_matches,
    )
