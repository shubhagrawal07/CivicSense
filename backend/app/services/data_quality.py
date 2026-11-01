from datetime import date, timedelta

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models import AuthorityContact, Issue, Jurisdiction, Report
from app.models.enums import ProcessingStatus, VerificationStatus

WARD_TYPE = "ward"
OLD_CONTACT_DAYS = 90


def count_where(db: Session, model, *conditions) -> int:
    query = select(func.count()).select_from(model).where(*conditions)
    result = db.scalar(query)
    return result


def count_issues_outside_wards(db: Session) -> int | None:
    ward_count = count_where(db, Jurisdiction, Jurisdiction.type == WARD_TYPE)
    if ward_count == 0:
        return None

    inside_a_ward = exists().where(
        Jurisdiction.type == WARD_TYPE,
        func.ST_Contains(Jurisdiction.boundary, Issue.location),
    )

    issues_outside_count = count_where(
        db, Issue, Issue.location.is_not(None), ~inside_a_ward
    )
    return issues_outside_count


def data_quality_summary(db: Session) -> dict:
    cutoff = date.today() - timedelta(days=OLD_CONTACT_DAYS)

    reports_without_description = count_where(db, Report, Report.description.is_(None))
    reports_without_image = count_where(db, Report, Report.image_path.is_(None))
    reports_failed_processing = count_where(
        db, Report, Report.processing_status == ProcessingStatus.FAILED
    )

    issues_outside_any_ward = count_issues_outside_wards(db)

    contacts_unverified = count_where(
        db,
        AuthorityContact,
        AuthorityContact.verification_status == VerificationStatus.UNVERIFIED,
    )

    contacts_older_than_90_days = count_where(
        db, AuthorityContact, AuthorityContact.last_verified < cutoff
    )

    return {
        "reports_without_description": reports_without_description,
        "reports_without_image": reports_without_image,
        "reports_failed_processing": reports_failed_processing,
        "issues_outside_any_ward": issues_outside_any_ward,
        "contacts_unverified": contacts_unverified,
        "contacts_older_than_90_days": contacts_older_than_90_days,
    }
