# AI-generated test code
import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models import Issue, IssueReport, Report, StatusHistory, User
from app.models.enums import ClassificationSource, IssueStatus, ProcessingStatus
from app.seed import seed_authorities, seed_departments
from app.services.reports import create_report
from app.workers import pipeline

LAT, LNG = 28.6139, 77.2090
TEXT = "Large pothole near the main gate, two scooters already slipped"


@pytest.fixture
def user(db):
    row = User(
        name="T", email="pipe@example.com", password_hash=hash_password("x" * 10)
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def seeded(db):
    seed_departments(db)
    seed_authorities(db)


@pytest.fixture
def fake_models(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "classify_text",
        lambda text: {
            "category": "pothole",
            "confidence": 0.9,
            "top_k": [],
            "needs_review": False,
        },
    )
    monkeypatch.setattr(
        pipeline,
        "classify_image",
        lambda path: {
            "category": "pothole",
            "confidence": 0.8,
            "raw_response": {},
            "needs_review": False,
        },
    )


def make_report(db, user, description=TEXT, image_name=None, dlat=0.0):
    return create_report(db, user.id, description, image_name, LAT + dlat, LNG)


def test_text_report_becomes_done_with_results(db, user, seeded, fake_models):
    report = make_report(db, user)

    pipeline.process_report(report.id, db)

    db.refresh(report)
    assert report.processing_status == ProcessingStatus.DONE
    assert report.processed_at is not None
    assert report.classification == "pothole"
    assert report.classification_source == ClassificationSource.TEXT
    assert report.predicted_department_id is not None
    assert report.predicted_severity is not None

    link = db.scalar(select(IssueReport).where(IssueReport.report_id == report.id))
    issue = db.get(Issue, link.issue_id)
    assert issue.report_count == 1
    assert issue.authority_id is not None
    assert issue.severity_score is not None

    history = db.scalars(
        select(StatusHistory).where(StatusHistory.issue_id == issue.id)
    ).all()
    assert len(history) == 1
    assert history[0].new_status == IssueStatus.NEW


def test_agreeing_image_and_text_use_both(db, user, seeded, fake_models):
    report = make_report(db, user, image_name="photo.png")

    pipeline.process_report(report.id, db)

    db.refresh(report)
    assert report.processing_status == ProcessingStatus.DONE
    assert report.classification_source == ClassificationSource.BOTH
    assert report.conflict is False


def test_conflicting_image_wins_and_is_flagged(
    db, user, seeded, fake_models, monkeypatch
):
    monkeypatch.setattr(
        pipeline,
        "classify_image",
        lambda path: {
            "category": "garbage",
            "confidence": 0.9,
            "raw_response": {},
            "needs_review": False,
        },
    )
    report = make_report(db, user, image_name="photo.png")

    pipeline.process_report(report.id, db)

    db.refresh(report)
    assert report.classification == "garbage"
    assert report.classification_source == ClassificationSource.IMAGE
    assert report.conflict is True
    assert report.needs_review is True


def test_failed_image_call_is_ignored(db, user, seeded, fake_models, monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "classify_image",
        lambda path: {
            "category": "other",
            "confidence": 0.0,
            "raw_response": "claude api error",
            "needs_review": True,
        },
    )
    report = make_report(db, user, image_name="photo.png")

    pipeline.process_report(report.id, db)

    db.refresh(report)
    assert report.classification == "pothole"
    assert report.classification_source == ClassificationSource.TEXT
    assert report.conflict is False


def test_nearby_report_links_to_same_issue(db, user, seeded, fake_models):
    first = make_report(db, user)
    second = make_report(db, user, dlat=0.0002)

    pipeline.process_report(first.id, db)
    pipeline.process_report(second.id, db)

    first_link = db.scalar(select(IssueReport).where(IssueReport.report_id == first.id))
    second_link = db.scalar(
        select(IssueReport).where(IssueReport.report_id == second.id)
    )
    assert first_link.issue_id == second_link.issue_id
    issue = db.get(Issue, first_link.issue_id)
    assert issue.report_count == 2
    history = db.scalars(
        select(StatusHistory).where(StatusHistory.issue_id == issue.id)
    ).all()
    assert len(history) == 1


def test_failing_stage_marks_report_failed_and_keeps_it(
    db, user, seeded, fake_models, monkeypatch
):
    def broken(text):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(pipeline, "classify_text", broken)
    report = make_report(db, user)

    pipeline.process_report(report.id, db)

    kept = db.get(Report, report.id)
    assert kept is not None
    assert kept.processing_status == ProcessingStatus.FAILED
    assert "model exploded" in kept.error
    assert kept.processed_at is not None
    link = db.scalar(select(IssueReport).where(IssueReport.report_id == report.id))
    assert link is None


def test_authority_lookup_failure_still_finishes(
    db, user, seeded, fake_models, monkeypatch
):
    def broken(*args):
        raise RuntimeError("lookup down")

    monkeypatch.setattr(pipeline, "lookup_authority", broken)
    report = make_report(db, user)

    pipeline.process_report(report.id, db)

    db.refresh(report)
    assert report.processing_status == ProcessingStatus.DONE
    link = db.scalar(select(IssueReport).where(IssueReport.report_id == report.id))
    assert db.get(Issue, link.issue_id).authority_id is None


def test_finished_report_is_not_processed_twice(db, user, seeded, fake_models):
    report = make_report(db, user)
    pipeline.process_report(report.id, db)
    finished_at = report.processed_at

    pipeline.process_report(report.id, db)

    db.refresh(report)
    assert report.processing_status == ProcessingStatus.DONE
    assert report.processed_at == finished_at


def test_missing_report_is_skipped(db):
    pipeline.process_report(999999, db)


def test_requeue_processes_only_unfinished_reports(db, user, monkeypatch):
    pending = make_report(db, user)
    processing = make_report(db, user)
    processing.processing_status = ProcessingStatus.PROCESSING
    done = make_report(db, user)
    done.processing_status = ProcessingStatus.DONE
    failed = make_report(db, user)
    failed.processing_status = ProcessingStatus.FAILED
    db.flush()

    class SessionStub:
        def __enter__(self):
            return db

        def __exit__(self, *args):
            return False

    seen = []
    monkeypatch.setattr(pipeline, "SessionLocal", SessionStub)
    monkeypatch.setattr(
        pipeline, "process_report", lambda report_id: seen.append(report_id)
    )

    pipeline.requeue_stuck_reports()

    assert pending.id in seen
    assert processing.id in seen
    assert done.id not in seen
    assert failed.id not in seen
