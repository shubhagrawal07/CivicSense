from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import IssueStatus, Severity


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100))
    location = mapped_column(Geometry("POINT", srid=4326))

    severity: Mapped[Severity | None] = mapped_column(Enum(Severity, name="severity"))
    severity_score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[IssueStatus] = mapped_column(
        Enum(IssueStatus, name="issue_status"), default=IssueStatus.NEW, index=True
    )

    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    authority_id: Mapped[int | None] = mapped_column(ForeignKey("authorities.id"))

    report_count: Mapped[int] = mapped_column(Integer, default=0)
    first_reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reports: Mapped[list["IssueReport"]] = relationship(back_populates="issue")


class IssueReport(Base):
    __tablename__ = "issue_reports"
    __table_args__ = (UniqueConstraint("report_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    match_score: Mapped[float | None] = mapped_column(Float)
    matching_method: Mapped[str | None] = mapped_column(String(50))
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    issue: Mapped["Issue"] = relationship(back_populates="reports")
