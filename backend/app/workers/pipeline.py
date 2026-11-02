import logging
import time
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.intelligence.fusion import fuse_predictions
from app.intelligence.image_classifier import classify_image
from app.intelligence.severity import compute_severity
from app.intelligence.text_classifier import classify_text
from app.models import Report, StatusHistory
from app.models.enums import ClassificationSource, IssueStatus, ProcessingStatus
from app.services.authority import lookup_authority
from app.services.issue_linking import link_or_create_issue

logger = logging.getLogger(__name__)

MAX_ERROR_LENGTH = 500


def get_text_prediction(report):
    if not report.description:
        return None
    return classify_text(report.description)


def get_image_prediction(report):
    if not report.image_name:
        return None
    result = classify_image(settings.upload_path / report.image_name)
    if result["confidence"] == 0.0 and result["needs_review"]:
        return None
    return result


def stage_classify(db, report):
    text_pred = get_text_prediction(report)
    image_pred = get_image_prediction(report)
    result = fuse_predictions(db, text_pred, image_pred)

    source = None
    if result["source"]:
        source = ClassificationSource(result["source"].upper())

    report.classification = result["category"]
    report.classification_confidence = result["confidence"]
    report.classification_source = source
    report.needs_review = result["needs_review"]
    report.conflict = result["conflict"]
    report.predicted_department_id = result["department"]["department_id"]
    report.department_confidence = result["department"]["confidence"]


def stage_severity(db, report):
    has_image = report.image_name is not None
    result = compute_severity(report.classification, report.description, has_image)
    report.predicted_severity = result["level"]
    return result


def stage_link(db, report, severity):
    link = link_or_create_issue(db, report)
    issue = link.issue

    if link.is_new:
        issue.severity_score = severity["score"]
        history = StatusHistory(
            issue_id=issue.id,
            old_status=None,
            new_status=IssueStatus.NEW,
            note=f"Issue created from report {report.id}",
        )
        db.add(history)
        return issue

    if issue.severity_score is None or severity["score"] > issue.severity_score:
        issue.severity = severity["level"]
        issue.severity_score = severity["score"]
    return issue


def stage_authority(db, report, issue):
    lng, lat = db.execute(
        select(func.ST_X(Report.location), func.ST_Y(Report.location)).where(
            Report.id == report.id
        )
    ).one()

    try:
        match = lookup_authority(db, report.predicted_department_id, lat, lng)
    except Exception:
        logger.exception("authority lookup failed for report %s", report.id)
        return

    if match.authority is not None:
        issue.authority_id = match.authority.id


def run_stage(name, report_id, function, *args):
    start = time.perf_counter()
    result = function(*args)
    seconds = time.perf_counter() - start
    logger.info("report %s stage %s took %.3fs", report_id, name, seconds)
    return result


def run_stages(db, report):
    run_stage("classify", report.id, stage_classify, db, report)
    severity = run_stage("severity", report.id, stage_severity, db, report)
    issue = run_stage("link", report.id, stage_link, db, report, severity)
    run_stage("authority", report.id, stage_authority, db, report, issue)


def mark_failed(db, report_id, message):
    db.rollback()
    report = db.get(Report, report_id)
    if report is None:
        return
    report.processing_status = ProcessingStatus.FAILED
    report.error = message[:MAX_ERROR_LENGTH]
    report.processed_at = datetime.now(timezone.utc)
    db.commit()


def run_pipeline(db, report_id):
    report = db.get(Report, report_id)
    if report is None:
        logger.warning("report %s not found", report_id)
        return
    if report.processing_status not in (
        ProcessingStatus.PENDING,
        ProcessingStatus.PROCESSING,
    ):
        return

    report.processing_status = ProcessingStatus.PROCESSING
    report.error = None
    db.commit()

    start = time.perf_counter()
    try:
        run_stages(db, report)
        report.processing_status = ProcessingStatus.DONE
        report.processed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as error:
        logger.exception("report %s failed", report_id)
        mark_failed(db, report_id, f"{type(error).__name__}: {error}")
        return

    logger.info("report %s done in %.3fs", report_id, time.perf_counter() - start)


def process_report(report_id: int, db: Session | None = None) -> None:
    if db is not None:
        run_pipeline(db, report_id)
        return
    with SessionLocal() as session:
        run_pipeline(session, report_id)


def requeue_stuck_reports() -> None:
    unfinished = [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]
    try:
        with SessionLocal() as db:
            ids = db.scalars(
                select(Report.id)
                .where(Report.processing_status.in_(unfinished))
                .order_by(Report.id)
            ).all()
    except Exception:
        logger.exception("could not look for stuck reports")
        return

    logger.info("re-queueing %s stuck reports", len(ids))
    for report_id in ids:
        process_report(report_id)
