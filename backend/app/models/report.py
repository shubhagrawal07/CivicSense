from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import ClassificationSource, ProcessingStatus, Severity


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String(500))
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
