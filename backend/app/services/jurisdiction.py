import json

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.models import Authority, Jurisdiction
from app.models.enums import JurisdictionStatus

SIMPLIFY_DEGREES = 0.0001


def list_jurisdictions(db: Session, type: str | None, status: JurisdictionStatus):
    shape = func.ST_AsGeoJSON(
        func.ST_SimplifyPreserveTopology(Jurisdiction.boundary, SIMPLIFY_DEGREES)
    )
    stmt = (
        select(
            Jurisdiction.id, Jurisdiction.name, Jurisdiction.type, shape, Authority.name
        )
        .outerjoin(Authority, Jurisdiction.authority_id == Authority.id)
        .where(Jurisdiction.status == status)
        .order_by(Jurisdiction.id)
    )
    if type is not None:
        stmt = stmt.where(Jurisdiction.type == type)

    features = []
    for row in db.execute(stmt):
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(row[3]),
                "properties": {
                    "id": row[0],
                    "name": row[1],
                    "type": row[2],
                    "authority_name": row[4],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def jurisdictions_at(db: Session, lat: float, lng: float):
    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    area = func.ST_Area(cast(Jurisdiction.boundary, Geography))
    stmt = (
        select(Jurisdiction, Authority)
        .outerjoin(Authority, Jurisdiction.authority_id == Authority.id)
        .where(Jurisdiction.status == JurisdictionStatus.APPROVED)
        .where(func.ST_Contains(Jurisdiction.boundary, point))
        .order_by(Jurisdiction.priority.desc(), area, Jurisdiction.id)
    )

    result = []
    for jurisdiction, authority in db.execute(stmt):
        result.append(
            {
                "id": jurisdiction.id,
                "name": jurisdiction.name,
                "type": jurisdiction.type,
                "priority": jurisdiction.priority,
                "authority": authority,
            }
        )
    return result
