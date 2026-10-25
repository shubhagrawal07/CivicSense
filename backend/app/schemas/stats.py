from pydantic import BaseModel


class SummaryOut(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    avg_resolution_days: float | None
