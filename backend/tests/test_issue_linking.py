from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, text

from app.core.config import settings
from app.models import Issue, IssueReport, Report, User
from app.models.enums import IssueStatus
from app.services.issue_linking import (
    METHOD_GEO,
    METHOD_NEW,
    MissingCategory,
    link_or_create_issue,
)

LAT, LNG = 19.1334, 72.9133
# one degree of latitude is about 111 km, so this is roughly 22 m
NEAR = 0.0002
FAR = 0.002


@pytest.fixture
def user(db):
    row = User(name="T", email="link@example.com", password_hash="x")
    db.add(row)
    db.flush()
    return row


def point(lat, lng):
    return func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)


def make_report(db, user, category="pothole", dlat=0.0, dlng=0.0):
    report = Report(
        user_id=user.id,
        description="x" * 12,
        location=point(LAT + dlat, LNG + dlng),
        classification=category,
    )
    db.add(report)
    db.flush()
    return report


def make_issue(db, category="pothole", status=IssueStatus.NEW, age_days=0, dlat=0.0):
    seen = datetime.now(timezone.utc) - timedelta(days=age_days)
    issue = Issue(
        category=category,
        location=point(LAT + dlat, LNG),
        status=status,
        report_count=1,
        first_reported_at=seen,
        last_reported_at=seen,
    )
    db.add(issue)
    db.flush()
    return issue


def test_first_report_creates_a_new_issue(db, user):
    report = make_report(db, user)

    result = link_or_create_issue(db, report)

    assert result.is_new
    assert result.method == METHOD_NEW
    assert result.issue.status == IssueStatus.NEW
    assert result.issue.category == "pothole"
    assert result.issue.report_count == 1
    assert result.issue.first_reported_at is not None


def test_two_nearby_same_category_reports_share_an_issue(db, user):
    first = link_or_create_issue(db, make_report(db, user))
    second = link_or_create_issue(db, make_report(db, user, dlat=NEAR))

    assert not second.is_new
    assert second.issue.id == first.issue.id
    assert second.issue.report_count == 2
    assert second.method == METHOD_GEO
    assert 0 < second.match_score <= 1


def test_link_row_stores_score_and_method(db, user):
    first = link_or_create_issue(db, make_report(db, user))
    report = make_report(db, user, dlat=NEAR)
    second = link_or_create_issue(db, report)

    link = db.scalar(select(IssueReport).where(IssueReport.report_id == report.id))
    assert link.issue_id == first.issue.id
    assert link.matching_method == METHOD_GEO
    assert link.match_score == second.match_score


def test_matching_updates_last_reported_at(db, user):
    issue = make_issue(db, age_days=10)
    before = issue.last_reported_at

    result = link_or_create_issue(db, make_report(db, user, dlat=NEAR))

    assert result.issue.id == issue.id
    assert result.issue.last_reported_at > before


def test_different_category_does_not_link(db, user):
    existing = db.scalar(select(func.count()).select_from(Issue))
    link_or_create_issue(db, make_report(db, user, "pothole"))
    other = link_or_create_issue(db, make_report(db, user, "garbage", dlat=NEAR))

    assert other.is_new
    assert db.scalar(select(func.count()).select_from(Issue)) == existing + 2


def test_far_away_report_does_not_link(db, user):
    first = link_or_create_issue(db, make_report(db, user))
    far = link_or_create_issue(db, make_report(db, user, dlat=FAR))

    assert far.is_new
    assert far.issue.id != first.issue.id


def test_issue_outside_time_window_does_not_link(db, user):
    old = make_issue(db, age_days=settings.link_window_days + 1)

    result = link_or_create_issue(db, make_report(db, user, dlat=NEAR))

    assert result.is_new
    assert result.issue.id != old.id


@pytest.mark.parametrize(
    "status",
    [
        IssueStatus.RESOLVED,
        IssueStatus.VERIFIED,
        IssueStatus.CLOSED,
        IssueStatus.DUPLICATE,
        IssueStatus.REJECTED,
    ],
)
def test_closed_issue_does_not_link(db, user, status):
    closed = make_issue(db, status=status)

    result = link_or_create_issue(db, make_report(db, user, dlat=NEAR))

    assert result.is_new
    assert result.issue.id != closed.id


@pytest.mark.parametrize("status", [IssueStatus.IN_PROGRESS, IssueStatus.REOPENED])
def test_open_statuses_still_link(db, user, status):
    issue = make_issue(db, status=status)

    result = link_or_create_issue(db, make_report(db, user, dlat=NEAR))

    assert result.issue.id == issue.id


def test_nearest_of_several_matches_wins(db, user):
    farther = make_issue(db, dlat=0.0003)
    nearer = make_issue(db, dlat=0.0001)

    result = link_or_create_issue(db, make_report(db, user))

    assert result.issue.id == nearer.id
    assert result.issue.id != farther.id


def test_radius_is_configurable(db, user, monkeypatch):
    make_issue(db)
    monkeypatch.setattr(settings, "link_radius_m", 10)

    result = link_or_create_issue(db, make_report(db, user, dlat=NEAR))

    assert result.is_new


def test_window_is_configurable(db, user, monkeypatch):
    make_issue(db, age_days=5)
    monkeypatch.setattr(settings, "link_window_days", 3)

    assert link_or_create_issue(db, make_report(db, user, dlat=NEAR)).is_new


def test_closer_match_scores_higher(db, user):
    make_issue(db)
    close = link_or_create_issue(db, make_report(db, user, dlat=0.00005))
    make_issue(db, category="garbage")
    edge = link_or_create_issue(db, make_report(db, user, "garbage", dlat=0.00040))

    assert close.match_score > edge.match_score


def test_weights_change_the_score(db, user, monkeypatch):
    make_issue(db)
    base = link_or_create_issue(db, make_report(db, user, dlat=NEAR)).match_score
    make_issue(db, category="garbage")
    monkeypatch.setattr(settings, "link_weight_geo", 5.0)
    heavy = link_or_create_issue(db, make_report(db, user, "garbage", dlat=NEAR))

    assert heavy.match_score != base


def test_report_without_category_is_refused(db, user):
    report = make_report(db, user, category=None)

    with pytest.raises(MissingCategory):
        link_or_create_issue(db, report)


def test_bbox_prefilter_can_use_the_spatial_index(db):
    db.execute(text("SET LOCAL enable_seqscan = off"))
    plan = db.execute(
        text(
            "EXPLAIN SELECT id FROM issues WHERE location && "
            "ST_Expand(ST_SetSRID(ST_MakePoint(72.9, 19.1), 4326), 0.001)"
        )
    ).fetchall()

    assert any("idx_issues_location" in row[0] for row in plan)
