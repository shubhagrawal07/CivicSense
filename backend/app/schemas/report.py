from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ClassificationSource, ProcessingStatus, Severity
from app.schemas.authority import ContactOut


class ReportAccepted(BaseModel):
    id: int
    processing_status: ProcessingStatus
    created_at: datetime


class LatLng(BaseModel):
    lat: float
    lng: float


class PartialPrediction(BaseModel):
    category: str
    confidence: float


class ClassificationOut(BaseModel):
    category: str
    confidence: float | None
    needs_review: bool
    source: ClassificationSource | None
    conflict: bool
    text: PartialPrediction | None = None
    image: PartialPrediction | None = None


class DepartmentRef(BaseModel):
    id: int
    name: str
    confidence: float | None


class SeverityOut(BaseModel):
    level: Severity
    score: float | None
    reasons: list[str]


class IssueRef(BaseModel):
    id: int
    status: str
    report_count: int
    is_new: bool


class AuthorityRef(BaseModel):
    name: str
    contacts: list[ContactOut]


class ReportOut(BaseModel):
    id: int
    description: str | None
    image_url: str | None
    location: LatLng
    created_at: datetime
    processing_status: ProcessingStatus
    error: str | None
    classification: ClassificationOut | None
    department: DepartmentRef | None
    severity: SeverityOut | None
    issue: IssueRef | None
    authority: AuthorityRef | None
