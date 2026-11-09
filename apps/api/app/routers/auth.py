import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_session, get_current_user
from app.errors import conflict, unauthorized
from app.models import User, UserSession
from app.security import (
    DUMMY_PASSWORD_HASH,
    SESSION_TTL,
    clear_session_cookie,
    hash_password,
    hash_token,
    new_session_token,
    set_session_cookie,
    verify_password,
)
from app.serializers import user_out

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VERSION_RE = re.compile(r"^[a-z0-9]{2,20}$")
INVALID_LOGIN = "E-mail ou senha incorretos."
EMAIL_TAKEN = "Já existe uma conta com este e-mail."


def normalize_email(value: str) -> str:
    return value.strip().lower()


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= 80:
            raise ValueError("O nome deve ter de 1 a 80 caracteres.")
        return value

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        value = normalize_email(value)
        if len(value) > 254 or not EMAIL_RE.match(value):
            raise ValueError("Informe um e-mail válido.")
        return value

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("A senha precisa ter pelo menos 8 caracteres.")
        if len(value) > 128:
            raise ValueError("A senha pode ter no máximo 128 caracteres.")
        return value


class LoginIn(BaseModel):
    email: str
    password: str


class MeUpdateIn(BaseModel):
    bible_version: str

    @field_validator("bible_version")
    @classmethod
    def check_version(cls, value: str) -> str:
        if not VERSION_RE.match(value):
            raise ValueError("Versão bíblica inválida.")
        return value


def start_session(db: Session, user: User, response: Response) -> None:
    token = new_session_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(timezone.utc) + SESSION_TTL,
        )
    )
    db.commit()
    set_session_cookie(response, token)


@router.post("/register", status_code=201)
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(User.id).where(User.email == body.email)):
        raise conflict(EMAIL_TAKEN)
    user = User(name=body.name, email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise conflict(EMAIL_TAKEN)
    start_session(db, user, response)
    return user_out(user)


@router.post("/login")
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == normalize_email(body.email)))
    if user is None:
        verify_password(DUMMY_PASSWORD_HASH, body.password)
        raise unauthorized(INVALID_LOGIN)
    if not verify_password(user.password_hash, body.password):
        raise unauthorized(INVALID_LOGIN)
    start_session(db, user, response)
    return user_out(user)


@router.post("/logout", status_code=204)
def logout(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)) -> Response:
    db.delete(session)
    db.commit()
    response = Response(status_code=204)
    clear_session_cookie(response)
    return response


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return user_out(user)


@router.patch("/me")
def update_me(body: MeUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    user.bible_version = body.bible_version
    db.commit()
    return user_out(user)
