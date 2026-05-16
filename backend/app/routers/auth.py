"""Authentication routes: login, logout, and current-user lookup.

Uses server-side sessions (SQLite session rows + httpOnly cookie), not JWT.
Deviates from the original Bearer-token contract; see docs/api_contract.md.
"""

import secrets

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_user, get_session_id
from app.limiter import limiter
from app.models import Session as DbSession
from app.models import User
from app.schemas import LoginRequest, LoginResponse, MessageResponse, UserPublic
from app.security import (
    clear_session_cookie,
    session_expiry,
    set_session_cookie,
    verify_password,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> LoginResponse:
    """Validate credentials, create a session row, set the sid cookie.

  Response body returns the user only—never a token or password. Rate limit
  slows brute-force guessing. See THREAT_MODEL.md > "Stealing passwords".
  """
    email = body.email.lower()
    # Look up by lowercased email; we store it lowercased on insert too.
    user = session.exec(select(User).where(User.email == email)).first()

    # Verify the password ONLY if the user exists. We still return the same
    # generic 401 below whether the user is missing, disabled, or has the wrong
    # password - this prevents user enumeration.
    password_ok = user and verify_password(user.password_hash, body.password)
    if not user or user.status != "active" or not password_ok:
        logger.info("login_failed", email=email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid email or password"},
        )

    sid = secrets.token_hex(32)
    db_session = DbSession(id=sid, user_id=user.id, expires_at=session_expiry())
    session.add(db_session)
    session.commit()

    set_session_cookie(response, sid)
    logger.info("login_success", user_id=user.id, email=user.email)
    return LoginResponse(user=UserPublic.from_user(user))


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)) -> UserPublic:
    """Return the authenticated user; used by the frontend on page load."""
    return UserPublic.from_user(user)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> MessageResponse:
    """Delete the server-side session so the cookie cannot be replayed."""
    sid = get_session_id(request)
    if sid:
        db_session = session.exec(select(DbSession).where(DbSession.id == sid)).first()
        if db_session:
            session.delete(db_session)
            session.commit()
    clear_session_cookie(response)
    return MessageResponse(message="Logged out")
