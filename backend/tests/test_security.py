from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    InvalidToken,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.models.enums import UserRole


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setattr(
        settings, "jwt_secret", "test-secret-for-security-tests-0123456789"
    )


def make_user(**extra):
    fields = {"id": 7, "role": UserRole.CITIZEN, **extra}
    return User(**fields)


def test_verify_password():
    hashed = hash_password("correct horse")
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong horse", hashed)


def test_token_carries_id_and_role():
    token = create_access_token(make_user(role=UserRole.ADMIN))
    claims = decode_access_token(token)
    assert claims["sub"] == "7"
    assert claims["role"] == "ADMIN"


def test_expired_token_is_rejected():
    claims = {
        "sub": "7",
        "role": "CITIZEN",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=5),
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)
    with pytest.raises(InvalidToken):
        decode_access_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token(make_user())
    head, body, sig = token.split(".")
    flipped = "A" if sig[0] != "A" else "B"
    with pytest.raises(InvalidToken):
        decode_access_token(f"{head}.{body}.{flipped}{sig[1:]}")


def test_token_signed_with_another_secret_is_rejected():
    claims = {
        "sub": "7",
        "role": "ADMIN",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(
        claims, "some-other-secret-that-is-long-enough-x", algorithm=ALGORITHM
    )
    with pytest.raises(InvalidToken):
        decode_access_token(token)


def test_empty_secret_refuses_to_sign(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "")
    with pytest.raises(RuntimeError):
        create_access_token(make_user())
