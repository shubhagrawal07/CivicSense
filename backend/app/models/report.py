from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import ClassificationSource, ProcessingStatus, Severity


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    location = mapped_column(Geometry("POINT", srid=4326))

    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status"),
        default=ProcessingStatus.PENDING,
    )
    error: Mapped[str | None] = mapped_column(Text)

    classification: Mapped[str | None] = mapped_column(String(100))
    classification_confidence: Mapped[float | None] = mapped_column(Float)
    classification_source: Mapped[ClassificationSource | None] = mapped_column(
        Enum(ClassificationSource, name="classification_source")
    )
    conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)

    predicted_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id")
    )
    department_confidence: Mapped[float | None] = mapped_column(Float)
    predicted_severity: Mapped[Severity | None] = mapped_column(
        Enum(Severity, name="severity")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    images: Mapped[list["ReportImage"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportImage.position, ReportImage.id",
    )

    @property
    def image_name(self) -> str | None:
        if self.images:
            return self.images[0].file_name
        return None


class ReportImage(Base):
    __tablename__ = "report_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    file_name: Mapped[str] = mapped_column(String(500))
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    report: Mapped["Report"] = relationship(back_populates="images")
