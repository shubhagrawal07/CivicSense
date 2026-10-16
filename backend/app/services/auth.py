from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import User
from app.models.enums import UserRole


class EmailTaken(Exception):
    pass


class BadCredentials(Exception):
    pass


# checked when the email is unknown, so a miss takes about as long as a wrong password
_DUMMY_HASH = hash_password("not-a-real-account")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, name: str, email: str, password: str) -> User:
    email = normalize_email(email)
    if db.scalar(select(User.id).where(User.email == email)):
        raise EmailTaken()

    user = User(
        name=name.strip(),
        email=email,
        password_hash=hash_password(password),
        role=UserRole.CITIZEN,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # two requests with the same email can both pass the check above
        db.rollback()
        raise EmailTaken() from None
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None:
        verify_password(password, _DUMMY_HASH)
        raise BadCredentials()
    if not verify_password(password, user.password_hash):
        raise BadCredentials()
    return user
