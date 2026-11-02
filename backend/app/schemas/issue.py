from datetime import datetime

from pydantic import BaseModel

from app.models.enums import IssueStatus, Severity
from app.schemas.authority import AuthorityOut, ContactOut, DepartmentOut
from app.schemas.report import LatLng


class StatusHistoryOut(BaseModel):
    status: IssueStatus
    changed_at: datetime
    note: str | None


class IssueOut(BaseModel):
    id: int
    category: str
    severity: Severity | None
    status: IssueStatus
    location: LatLng
    report_count: int
    first_reported_at: datetime
    last_reported_at: datetime
    department: DepartmentOut | None
    authority: AuthorityOut | None
    contacts: list[ContactOut]
    status_history: list[StatusHistoryOut]
