"""Password hashing and session-cookie helpers.

Passwords are hashed with argon2 (OWASP-recommended). Session cookies are
httpOnly + SameSite=Lax so JavaScript cannot read them, even if XSS slipped
through.
"""

from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Response

from app.config import get_settings

ph = PasswordHasher()
settings = get_settings()


def hash_password(password: str) -> str:
    """Return an argon2 hash suitable for storage in user.password_hash."""
    return ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Check a plaintext password against a stored hash without raising on mismatch."""
    try:
        ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def session_expiry() -> datetime:
    """UTC timestamp when a newly created session row should be considered expired."""
    return datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours)


def set_session_cookie(response: Response, session_id: str) -> None:
    """Attach the session id as an httpOnly cookie (not a Bearer token in JSON).

    We use server-side sessions + cookies instead of JWT in localStorage because
    logout and account disable take effect immediately, and JS cannot read the
    sid. Secure is off on localhost (COOKIE_SECURE=false); enable in production.
    """
    max_age = settings.session_ttl_hours * 3600
    response.set_cookie(
        key=settings.cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=max_age,
    )


def clear_session_cookie(response: Response) -> None:
    """Remove the session cookie on logout (must match set_session_cookie flags)."""
    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
