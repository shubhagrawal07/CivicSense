from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.errors import InvalidInput
from app.intelligence.severity import compute_severity
from app.models import Department, Issue, IssueReport, Report, ReportImage
from app.models.enums import ProcessingStatus
from app.schemas.report import (
    AuthorityRef,
    ClassificationOut,
    DepartmentRef,
    IssueRef,
    LatLng,
    MyReportItem,
    MyReportsPage,
    ReportOut,
    SeverityOut,
)
from app.services.authority import contacts_out, lookup_authority
from app.services.issue_linking import METHOD_NEW

MIN_DESCRIPTION = 10
MAX_DESCRIPTION = 1000
PREVIEW_LENGTH = 100


def clean_description(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    if len(text) < MIN_DESCRIPTION:
        raise InvalidInput(
            "description", f"Description must be at least {MIN_DESCRIPTION} characters"
        )
    if len(text) > MAX_DESCRIPTION:
        raise InvalidInput(
            "description", f"Description must be at most {MAX_DESCRIPTION} characters"
        )
    return text


def check_region(lat: float, lng: float) -> None:
    s = settings
    bounds = (s.region_min_lat, s.region_max_lat, s.region_min_lng, s.region_max_lng)
    if None in bounds:
        return
    if not (bounds[0] <= lat <= bounds[1] and bounds[2] <= lng <= bounds[3]):
        raise InvalidInput("latitude", "Location is outside the supported region")


def create_report(
    db: Session,
    user_id: int,
    description: str | None,
    image_name: str | None,
    lat: float,
    lng: float,
) -> Report:
    report = Report(
        user_id=user_id,
        description=description,
        location=func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
        processing_status=ProcessingStatus.PENDING,
    )
    if image_name:
        report.images.append(ReportImage(file_name=image_name, position=0))
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def build_report_out(db: Session, report: Report) -> ReportOut:
    lng, lat = db.execute(
        select(func.ST_X(Report.location), func.ST_Y(Report.location)).where(
            Report.id == report.id
        )
    ).one()
    out = ReportOut(
        id=report.id,
        description=report.description,
        image_url=f"/uploads/{report.image_name}" if report.image_name else None,
        location=LatLng(lat=lat, lng=lng),
        created_at=report.created_at,
        processing_status=report.processing_status,
        error=report.error,
        classification=None,
        department=None,
        severity=None,
        issue=None,
        authority=None,
    )
    if report.processing_status != ProcessingStatus.DONE:
        return out

    if report.classification:
        out.classification = ClassificationOut(
            category=report.classification,
            confidence=report.classification_confidence,
            needs_review=report.needs_review,
            source=report.classification_source,
            conflict=report.conflict,
        )

    department = None
    if report.predicted_department_id:
        department = db.get(Department, report.predicted_department_id)
    if department:
        out.department = DepartmentRef(
            id=department.id,
            name=department.name,
            confidence=report.department_confidence,
        )

    row = db.execute(
        select(Issue, IssueReport.matching_method)
        .join(IssueReport)
        .where(IssueReport.report_id == report.id)
    ).first()
    if row:
        issue, method = row
        out.issue = IssueRef(
            id=issue.id,
            status=issue.status.value,
            report_count=issue.report_count,
            is_new=method == METHOD_NEW,
        )

    if report.predicted_severity:
        severity = compute_severity(
            report.classification, report.description, report.image_name is not None
        )
        out.severity = SeverityOut(
            level=report.predicted_severity,
            score=severity["score"],
            reasons=severity["reasons"],
        )

    if department:
        match = lookup_authority(db, department.id, lat, lng)
        if match.authority:
            out.authority = AuthorityRef(
                name=match.authority.name,
                contacts=contacts_out(match.contacts),
            )
    return out


def list_my_reports(
    db: Session, user_id: int, limit: int, offset: int
) -> MyReportsPage:

    total = db.scalar(
        select(func.count()).select_from(Report).where(Report.user_id == user_id)
    )

    rows = db.execute(
        select(Report, Issue)
        .outerjoin(IssueReport, IssueReport.report_id == Report.id)
        .outerjoin(Issue, Issue.id == IssueReport.issue_id)
        .where(Report.user_id == user_id)
        .options(selectinload(Report.images))
        .order_by(Report.created_at.desc(), Report.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    items = []
    for report, issue in rows:
        preview = None
        if report.description:
            preview = report.description[:PREVIEW_LENGTH]
        thumbnail = None
        if report.image_name:
            thumbnail = f"/uploads/{report.image_name}"

        item = MyReportItem(
            id=report.id,
            description_preview=preview,
            thumbnail_url=thumbnail,
            created_at=report.created_at,
            processing_status=report.processing_status,
        )
        if report.processing_status == ProcessingStatus.DONE:
            item.category = report.classification
            item.severity_level = report.predicted_severity
            if issue:
                item.issue_id = issue.id
                item.issue_status = issue.status.value
                item.report_count = issue.report_count
        items.append(item)

    return MyReportsPage(items=items, total=total)
