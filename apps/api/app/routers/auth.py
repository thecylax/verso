import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_session, get_current_user
from app.errors import conflict, forbidden, unauthorized
from app.models import Invite, User, UserSession
from app.security import (
    DUMMY_PASSWORD_HASH,
    INVITE_TTL,
    SESSION_TTL,
    clear_session_cookie,
    hash_password,
    hash_token,
    new_session_token,
    set_session_cookie,
    verify_password,
)
from app.serializers import iso, user_out

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VERSION_RE = re.compile(r"^[a-z0-9]{2,20}$")
INVALID_LOGIN = "E-mail ou senha incorretos."
EMAIL_TAKEN = "Já existe uma conta com este e-mail."
NEED_INVITE = "Cadastro só é possível com um convite."
INVITE_INVALID = "Convite inválido ou já utilizado."
INVITE_EXPIRED = "Este convite expirou."
INVITE_FORBIDDEN = "Você não pode gerar convites."


def normalize_email(value: str) -> str:
    return value.strip().lower()


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str
    invite: str | None = None

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

    @field_validator("invite")
    @classmethod
    def check_invite(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or len(value) > 200:
            raise ValueError("Convite inválido.")
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


def usable_invite(db: Session, token: str) -> Invite:
    invite = db.scalar(select(Invite).where(Invite.token_hash == hash_token(token)))
    if invite is None or invite.used_at is not None:
        raise forbidden(INVITE_INVALID)
    if invite.expires_at <= datetime.now(timezone.utc):
        raise forbidden(INVITE_EXPIRED)
    return invite


@router.post("/invites", status_code=201)
def create_invite(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    if not user.can_invite:
        raise forbidden(INVITE_FORBIDDEN)
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + INVITE_TTL
    db.add(Invite(token_hash=hash_token(token), created_by=user.id, expires_at=expires_at))
    db.commit()
    return {"token": token, "expires_at": iso(expires_at)}


@router.get("/invites/{token}")
def read_invite(token: str, db: Session = Depends(get_db)) -> dict:
    invite = usable_invite(db, token)
    return {"expires_at": iso(invite.expires_at)}


@router.post("/register", status_code=201)
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)) -> dict:
    first_account = db.scalar(select(func.count()).select_from(User)) == 0
    invite = None
    if first_account:
        can_invite = True
    else:
        if not body.invite:
            raise forbidden(NEED_INVITE)
        invite = usable_invite(db, body.invite)
        can_invite = False
    if db.scalar(select(User.id).where(User.email == body.email)):
        db.rollback()
        raise conflict(EMAIL_TAKEN)
    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        can_invite=can_invite,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise conflict(EMAIL_TAKEN)
    if invite is not None:
        invite.used_at = datetime.now(timezone.utc)
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
