from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import ContactType, SourceStatus, VerificationStatus


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class Authority(Base):
    __tablename__ = "authorities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    jurisdiction: Mapped[str] = mapped_column(String(200))

    department: Mapped["Department | None"] = relationship()
    contacts: Mapped[list["AuthorityContact"]] = relationship(
        back_populates="authority", cascade="all, delete-orphan"
    )


class AuthorityContact(Base):
    __tablename__ = "authority_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    authority_id: Mapped[int] = mapped_column(ForeignKey("authorities.id"))
    type: Mapped[ContactType] = mapped_column(Enum(ContactType, name="contact_type"))
    value: Mapped[str] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    last_verified: Mapped[date | None] = mapped_column(Date)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.UNVERIFIED,
    )

    authority: Mapped["Authority"] = relationship(back_populates="contacts")


class GovernmentSource(Base):
    __tablename__ = "government_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    authority_id: Mapped[int | None] = mapped_column(ForeignKey("authorities.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    jurisdiction: Mapped[str | None] = mapped_column(String(200))
    domain: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(1000))
    scraper_type: Mapped[str | None] = mapped_column(String(50))
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[SourceStatus] = mapped_column(
        Enum(SourceStatus, name="source_status"), default=SourceStatus.ACTIVE
    )
