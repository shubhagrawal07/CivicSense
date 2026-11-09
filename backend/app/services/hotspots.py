from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.intelligence.hotspots import (
    CELL_SIZE_DEGREES,
    DEFAULT_SEVERITY_WEIGHT,
    SEVERITY_WEIGHTS,
    recency_weight,
)
from app.models import Issue
from app.services.issues import filter_issues


def snap_to_grid(value):
    return round(round(value / CELL_SIZE_DEGREES) * CELL_SIZE_DEGREES, 3)


def hotspot_cells(
    db: Session, category: str | None = None, days: int = 90, limit: int = 20
):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).date()

    query = select(
        Issue.severity,
        Issue.last_reported_at,
        func.ST_X(Issue.location).label("lng"),
        func.ST_Y(Issue.location).label("lat"),
    ).where(Issue.location.is_not(None))
    query = filter_issues(query, category=category, start=start)

    cells = {}
    for row in db.execute(query):
        cell_key = (snap_to_grid(row.lat), snap_to_grid(row.lng))
        age_days = (now - row.last_reported_at).days
        weight = SEVERITY_WEIGHTS.get(
            row.severity, DEFAULT_SEVERITY_WEIGHT
        ) * recency_weight(age_days)

        cell = cells.setdefault(cell_key, {"count": 0, "score": 0.0})
        cell["count"] += 1
        cell["score"] += weight

    results = [
        {"lat": lat, "lng": lng, "count": cell["count"], "score": cell["score"]}
        for (lat, lng), cell in cells.items()
    ]
    results.sort(key=lambda cell: cell["score"], reverse=True)
    return results[:limit]
