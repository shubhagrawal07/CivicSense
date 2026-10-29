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
