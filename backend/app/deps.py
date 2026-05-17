"""FastAPI dependencies for authentication and role checks.

These run on every protected route before handler code. The server is the
security boundary; frontend guards are UX only.
"""

from datetime import UTC, datetime
from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.config import get_settings
from app.db import get_session
from app.models import Session as DbSession
from app.models import User

settings = get_settings()


def get_session_id(request: Request) -> str | None:
    """Read the session cookie set at login (name from config, default sid)."""
    return request.cookies.get(settings.cookie_name)


def current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    """Resolve the logged-in user from the sid cookie and session table.

    Returns 401 if the cookie is missing, unknown, expired, or tied to a
    disabled user. Expired rows are deleted eagerly so stale sessions do not
    accumulate.
    """
    sid = get_session_id(request)
    if not sid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Authentication required"},
        )

    db_session = session.exec(select(DbSession).where(DbSession.id == sid)).first()
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Authentication required"},
        )

    expires_at = db_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        session.delete(db_session)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Authentication required"},
        )

    user = session.get(User, db_session.user_id)
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Authentication required"},
        )

    return user


def require_role(*roles: str) -> Callable:
    """Factory: dependency that allows only users whose role is in roles.

    Must be used after current_user (it Depends on it). Non-matching roles
    get 403, not 401, because they are authenticated but not authorized.
    """

    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden"},
            )
        return user

    return dependency
