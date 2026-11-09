from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.enums import IssueStatus, Severity


class MapProperties(BaseModel):
    id: int
    category: str
    severity: Severity | None
    status: IssueStatus
    report_count: int
    last_reported_at: datetime


class PointGeometry(BaseModel):
    type: Literal["Point"]
    coordinates: list[float]


class MapFeature(BaseModel):
    type: Literal["Feature"]
    geometry: PointGeometry
    properties: MapProperties


class MapFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[MapFeature]
