from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import InvalidToken, decode_access_token
from app.models import Report, User
from app.models.enums import UserRole

# auto_error is off so a missing header gets the same 401 as a bad token
bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise _unauthorized()
    try:
        claims = decode_access_token(credentials.credentials)
        user_id = int(claims["sub"])
    except (InvalidToken, ValueError):
        raise _unauthorized() from None

    # role comes from the row, not the token, so a role change applies at once
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return user


def require_role(*roles: UserRole):
    def check(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Not allowed")
        return user

    return check


# 404 and not 403, so guessing report ids does not reveal which ones exist
def assert_owner_or_admin(user: User, report: Report) -> None:
    if user.role == UserRole.ADMIN or report.user_id == user.id:
        return
    raise HTTPException(status_code=404, detail="Report not found")
