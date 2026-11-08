from pydantic import BaseModel

from app.schemas.authority import AuthorityOut


class JurisdictionAtOut(BaseModel):
    id: int
    name: str
    type: str
    priority: int
    authority: AuthorityOut | None
