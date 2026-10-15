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


def test_hash_is_not_the_password():
    hashed = hash_password("hunter22hunter")
    assert hashed != "hunter22hunter"
    assert "hunter22hunter" not in hashed


def test_same_password_hashes_differently():
    assert hash_password("samepassword") != hash_password("samepassword")


def test_verify_password():
    hashed = hash_password("correct horse")
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong horse", hashed)


def test_verify_password_with_garbage_hash():
    assert not verify_password("anything", "not-a-real-hash")


def test_token_carries_id_and_role():
    token = create_access_token(make_user(role=UserRole.ADMIN))
    claims = decode_access_token(token)
    assert claims["sub"] == "7"
    assert claims["role"] == "ADMIN"


def test_token_expiry_follows_settings(monkeypatch):
    monkeypatch.setattr(settings, "jwt_expire_minutes", 5)
    claims = decode_access_token(create_access_token(make_user()))
    left = datetime.fromtimestamp(claims["exp"], timezone.utc) - datetime.now(
        timezone.utc
    )
    assert timedelta(minutes=4) < left <= timedelta(minutes=5)


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


def test_token_missing_claims_is_rejected():
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode({"sub": "7", "exp": exp}, settings.jwt_secret, ALGORITHM)
    with pytest.raises(InvalidToken):
        decode_access_token(token)


def test_garbage_token_is_rejected():
    with pytest.raises(InvalidToken):
        decode_access_token("definitely.not.a-token")


def test_empty_secret_refuses_to_sign(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "")
    with pytest.raises(RuntimeError):
        create_access_token(make_user())
