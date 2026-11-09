from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.security import hash_password
from app.models import Issue, IssueReport, Report, User
from app.models.enums import IssueStatus, ProcessingStatus
from app.seeds import generate_reports


def synthetic_reports(db):
    return db.scalars(select(Report).where(Report.is_synthetic)).all()


def synthetic_issues(db):
    return db.scalars(select(Issue).where(Issue.is_synthetic)).all()


def test_load_creates_expected_counts(db):
    generate_reports.load(db, count=200, seed=1)

    reports = synthetic_reports(db)
    issues = synthetic_issues(db)

    assert len(reports) == 200
    assert all(r.is_synthetic for r in reports)
    assert all(i.is_synthetic for i in issues)
    assert any(i.report_count > 1 for i in issues)


def test_status_and_resolved_at(db):
    generate_reports.load(db, count=300, seed=3)

    issues = synthetic_issues(db)
    statuses = {i.status for i in issues}

    assert statuses == {IssueStatus.NEW, IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED}
    for issue in issues:
        if issue.status == IssueStatus.RESOLVED:
            assert issue.resolved_at is not None
            assert issue.resolved_at > issue.first_reported_at
        else:
            assert issue.resolved_at is None


def make_real_report_and_issue(db):
    user = User(
        name="Real Citizen",
        email="real.citizen@example.com",
        password_hash=hash_password("not-synthetic"),
    )
    db.add(user)
    db.commit()

    report = Report(
        user_id=user.id,
        description="A real report",
        location=func.ST_SetSRID(func.ST_MakePoint(72.9, 19.1), 4326),
        processing_status=ProcessingStatus.DONE,
        classification="pothole",
        is_synthetic=False,
    )
    db.add(report)
    db.flush()

    issue = Issue(
        category="pothole",
        location=func.ST_SetSRID(func.ST_MakePoint(72.9, 19.1), 4326),
        status=IssueStatus.NEW,
        report_count=1,
        first_reported_at=datetime.now(timezone.utc),
        last_reported_at=datetime.now(timezone.utc),
        is_synthetic=False,
    )
    db.add(issue)
    db.flush()

    db.add(IssueReport(issue_id=issue.id, report_id=report.id, match_score=1.0))
    db.commit()
    return report.id, issue.id


def test_reset_removes_only_synthetic(db):
    real_report_id, real_issue_id = make_real_report_and_issue(db)
    generate_reports.load(db, count=50, seed=4)

    generate_reports.reset(db)

    assert synthetic_reports(db) == []
    assert synthetic_issues(db) == []
    assert db.get(Report, real_report_id) is not None
    assert db.get(Issue, real_issue_id) is not None


def test_is_synthetic_defaults_false(db):
    user = User(
        name="Plain Citizen",
        email="plain.citizen@example.com",
        password_hash=hash_password("not-synthetic"),
    )
    db.add(user)
    db.commit()

    report = Report(
        user_id=user.id,
        description="No flag set",
        location=func.ST_SetSRID(func.ST_MakePoint(72.9, 19.1), 4326),
    )
    db.add(report)
    db.commit()

    assert report.is_synthetic is False
