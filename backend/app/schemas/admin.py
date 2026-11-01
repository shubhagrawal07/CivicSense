from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import IssueStatus


class StatusUpdateIn(BaseModel):
    status: str
    note: str | None = Field(default=None, max_length=1000)


class IssueStatusOut(BaseModel):
    id: int
    status: IssueStatus
    updated_at: datetime


class DataQualityOut(BaseModel):
    reports_without_description: int
    reports_without_image: int
    reports_failed_processing: int
    issues_outside_any_ward: int | None
    contacts_unverified: int
    contacts_older_than_90_days: int
