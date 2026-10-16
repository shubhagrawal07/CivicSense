from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.models import Issue, User
from app.models.enums import IssueStatus as S
from app.services.auth import normalize_email
from app.services.issues import change_status

# one path per issue, taken in id order
PATHS = [
    [S.UNDER_REVIEW, S.ASSIGNED, S.IN_PROGRESS],
    [S.UNDER_REVIEW, S.ASSIGNED, S.IN_PROGRESS, S.RESOLVED],
    [S.REJECTED],
]


def main():
    with SessionLocal() as db:
        admin = db.scalar(
            select(User).where(User.email == normalize_email(settings.admin_email))
        )
        if admin is None:
            raise SystemExit(
                "no admin user, set ADMIN_EMAIL and run python -m app.seed"
            )

        issues = db.scalars(select(Issue).order_by(Issue.id).limit(len(PATHS))).all()
        if not issues:
            raise SystemExit("no issues yet, submit a few reports first")

        for issue, path in zip(issues, PATHS, strict=False):
            for status in path:
                before = issue.status.value
                change_status(db, issue.id, status, "demo", admin.id)
                print(f"issue {issue.id}: {before} -> {status.value}")


if __name__ == "__main__":
    main()
