from datetime import date

from pydantic import BaseModel

from app.models.enums import Severity


class SummaryOut(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    avg_resolution_days: float | None


class CategoryCount(BaseModel):
    category: str
    count: int


class SeverityCount(BaseModel):
    severity: Severity
    count: int


class BreakdownOut(BaseModel):
    by_category: list[CategoryCount]
    by_severity: list[SeverityCount]


class TrendPoint(BaseModel):
    period: date
    count: int


class WardCount(BaseModel):
    ward_id: int
    ward_name: str
    issue_count: int
    open_count: int
    high_severity_count: int
