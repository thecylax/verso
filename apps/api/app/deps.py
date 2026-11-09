from datetime import datetime, timezone

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import unauthorized
from app.models import User, UserSession
from app.security import SESSION_COOKIE, hash_token


def get_current_session(request: Request, db: Session = Depends(get_db)) -> UserSession:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise unauthorized()
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if session is None:
        raise unauthorized(clear_cookie=True)
    if session.expires_at <= datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise unauthorized(clear_cookie=True)
    return session


def get_current_user(
    session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)
) -> User:
    user = db.get(User, session.user_id)
    if user is None:
        raise unauthorized(clear_cookie=True)
    return user
