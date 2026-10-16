from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import IssueStatus


class StatusUpdateIn(BaseModel):
    # kept as a plain string so an unknown value is a 400 from our check, not a 422
    status: str
    note: str | None = Field(default=None, max_length=1000)


class IssueStatusOut(BaseModel):
    id: int
    status: IssueStatus
    updated_at: datetime
