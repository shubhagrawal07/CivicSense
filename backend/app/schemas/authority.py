from datetime import date

from pydantic import BaseModel, ConfigDict


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AuthorityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    jurisdiction: str


class ContactOut(BaseModel):
    type: str
    value: str
    source_url: str | None
    last_verified_at: date | None
    verified: bool


class AuthorityInfoOut(BaseModel):
    department: DepartmentOut
    authority: AuthorityOut | None
    contacts: list[ContactOut]
    is_fallback: bool
    needs_review: bool
    other_matches: list[AuthorityOut]
