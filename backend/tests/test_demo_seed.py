import pytest
from sqlalchemy import select

from app import demo_seed
from app.core.config import settings
from app.models import Issue, IssueReport, Report, StatusHistory, User
from app.models.enums import ProcessingStatus, Severity
from app.seed_data.demo_reports import REPORTS


@pytest.fixture
def loaded(db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    demo_seed.reset(db)
    demo_seed.load(db)


def demo_reports(db):
    return db.scalars(
        select(Report).join(User).where(User.email.like("demo.%@example.com"))
    ).all()


def test_load_covers_the_ticket(db, loaded, tmp_path):
    reports = demo_reports(db)
    done = [r for r in reports if r.processing_status == ProcessingStatus.DONE]

    assert len(reports) == len(REPORTS) + 1
    assert 30 <= len(reports) <= 50
    assert [r.processing_status for r in reports].count(ProcessingStatus.FAILED) == 1
    assert len({r.classification for r in done}) >= 9
    assert sum(r.needs_review for r in done) >= 3
    assert len(list(tmp_path.glob("demo_*.jpg"))) == sum(1 for r in REPORTS if r[4])


def test_load_makes_duplicates_severities_and_statuses(db, loaded):
    report_ids = [r.id for r in demo_reports(db)]
    mine = db.scalars(
        select(Issue)
        .join(IssueReport)
        .where(IssueReport.report_id.in_(report_ids))
        .distinct()
    ).all()

    assert max(i.report_count for i in mine) >= 3
    assert sum(1 for i in mine if i.report_count > 1) >= 5
    assert {Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL} <= {
        i.severity for i in mine
    }
    assert len({i.status for i in mine}) >= 6


def test_status_changes_are_attributed_to_the_admin(db, loaded):
    changed = db.scalars(
        select(StatusHistory).where(StatusHistory.changed_by.is_not(None))
    ).all()

    assert changed
    assert all(entry.created_at is not None for entry in changed)


def test_loading_twice_is_refused(db, loaded):
    with pytest.raises(SystemExit):
        demo_seed.load(db)


def test_reset_removes_the_demo_data(db, loaded, tmp_path):
    demo_seed.reset(db)

    assert demo_reports(db) == []
    assert list(tmp_path.glob("demo_*.jpg")) == []
