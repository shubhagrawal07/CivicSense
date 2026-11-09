from pydantic import BaseModel


class HotspotCell(BaseModel):
    lat: float
    lng: float
    count: int
    score: float
