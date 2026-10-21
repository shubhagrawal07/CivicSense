from dataclasses import dataclass, field
from datetime import date

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.models import Authority, Department, JurisdictionArea
from app.models.enums import VerificationStatus

EDGE_METRES = 30
# supplies the contacts when a department has nothing of its own
FALLBACK_DEPARTMENT = "General Grievance"


class DepartmentNotFound(Exception):
    pass


@dataclass
class ContactInfo:
    type: str
    value: str
    source_url: str | None
    last_verified: date | None
    verified: bool


@dataclass
class AuthorityMatch:
    department: Department
    authority: Authority | None
    contacts: list[ContactInfo]
    is_fallback: bool = False
    needs_review: bool = False
    other_matches: list[Authority] = field(default_factory=list)


def lookup_authority(db: Session, department_id: int, lat: float, lng: float):
    department = db.get(Department, department_id)
    if department is None:
        raise DepartmentNotFound(department_id)

    inside, near = areas_around(db, department_id, lat, lng)
    default = default_authority(db, department_id)

    if inside:
        top = max(inside.values())

        winners = []
        for key, score in inside.items():
            if score == top:
                winners.append(key)

        winners.sort(key=_by_id)

        best = winners[0]
        tied = winners[1:]
    else:
        best, tied = default, []

    others = []
    if tied or near:
        candidates = tied + sorted(near, key=_by_id)
        if near:
            candidates.append(default)
        for authority in candidates:
            if authority is not None and authority is not best:
                if authority not in others:
                    others.append(authority)

    contacts = contact_info(best) if best else []
    is_fallback = not contacts
    if is_fallback:
        contacts = fallback_contacts(db)

    return AuthorityMatch(
        department=department,
        authority=best,
        contacts=contacts,
        is_fallback=is_fallback,
        needs_review=bool(tied or near),
        other_matches=others,
    )


def areas_around(db, department_id, lat, lng):
    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    edge = func.ST_Distance(
        cast(func.ST_Boundary(JurisdictionArea.area), Geography),
        cast(point, Geography),
    )
    stmt = (
        select(
            Authority,
            JurisdictionArea.priority,
            func.ST_Covers(JurisdictionArea.area, point),
            edge,
        )
        .join(JurisdictionArea)
        .where(Authority.department_id == department_id)
    )
    inside = {}
    near = set()
    for authority, priority, covers, edge_m in db.execute(stmt):
        if covers:
            inside[authority] = max(inside.get(authority, priority), priority)
        if edge_m <= EDGE_METRES:
            near.add(authority)
    return inside, near


def default_authority(db, department_id):
    stmt = (
        select(Authority)
        .outerjoin(JurisdictionArea)
        .where(Authority.department_id == department_id)
        .where(JurisdictionArea.id.is_(None))
        .order_by(Authority.id)
    )
    return db.scalars(stmt).first()


def fallback_contacts(db):
    stmt = select(Department.id).where(Department.name == FALLBACK_DEPARTMENT)
    general_id = db.scalar(stmt)
    if general_id is None:
        return []
    authority = default_authority(db, general_id)
    if authority is None:
        return []
    return contact_info(authority, trusted=False)


def contact_info(authority, trusted=True):

    def my_sort_key(c):
        is_not_verified = c.verification_status != VerificationStatus.VERIFIED
        return (is_not_verified, c.id)

    contacts = sorted(authority.contacts, key=my_sort_key)

    result_list = []

    for c in contacts:
        is_verified = False
        if trusted == True:
            if c.verification_status == VerificationStatus.VERIFIED:
                is_verified = True

        info = ContactInfo(
            type=c.type.value,
            value=c.value,
            source_url=c.source_url,
            last_verified=c.last_verified,
            verified=is_verified,
        )
        result_list.append(info)
    return result_list


def _by_id(authority):
    return authority.id
