from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.security import create_access_token
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.services.auth import BadCredentials, EmailTaken, authenticate, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Annotated[Session, Depends(get_db)]):
    try:
        return register_user(db, body.name, body.email, body.password)
    except EmailTaken:
        raise HTTPException(
            status_code=409, detail="Email already registered"
        ) from None


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]):
    return user


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Annotated[Session, Depends(get_db)]):
    try:
        user = authenticate(db, body.email, body.password)
    except BadCredentials:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return TokenOut(access_token=create_access_token(user), user=user)
