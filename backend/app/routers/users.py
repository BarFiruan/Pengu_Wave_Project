"""User management CRUD. All routes require the admin role.

The router-level dependency ensures no /api/users handler runs without
admin, so a future endpoint cannot accidentally skip the check.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from app.db import get_session
from app.deps import current_user, require_role
from app.models import User
from app.schemas import (
    CreateUserRequest,
    MessageResponse,
    UpdateUserRequest,
    UserPublic,
)
from app.security import hash_password

# Every route under /api/users requires admin. The dependency is declared once
# at the router level so a future contributor can't accidentally add an admin
# endpoint without the check.
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(require_role("admin"))],
)


def _count_active_admins(session: Session) -> int:
    """Used to block deleting or demoting the last active admin."""
    statement = select(func.count()).select_from(User).where(
        User.role == "admin",
        User.status == "active",
    )
    return session.exec(statement).one()


@router.get("", response_model=list[UserPublic])
def list_users(session: Session = Depends(get_session)) -> list[UserPublic]:
    """List users via UserPublic so password_hash never enters the response."""
    users = session.exec(select(User).order_by(User.email)).all()
    return [UserPublic.from_user(u) for u in users]


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(
    body: CreateUserRequest,
    session: Session = Depends(get_session),
) -> UserPublic:
    """Create a user; only admins reach this handler (router dependency)."""
    email = body.email.lower()
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email already in use"},
        )

    user = User(
        id=uuid.uuid4().hex,
        email=email,
        password_hash=hash_password(body.password),
        role=body.role,
        status="active",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserPublic.from_user(user)


@router.patch("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: str,
    body: UpdateUserRequest,
    session: Session = Depends(get_session),
    current: User = Depends(current_user),
) -> UserPublic:
    """Update role and/or status only (enforced by UpdateUserRequest schema)."""
    if body.role is None and body.status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "No fields to update"},
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found"},
        )

    # Last-admin protection: cannot demote yourself if you are the only active admin.
    if body.role is not None and user.id == current.id and body.role != "admin":
        if _count_active_admins(session) <= 1 and user.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Cannot demote the last active admin"},
            )

    if body.role is not None:
        user.role = body.role
    if body.status is not None:
        user.status = body.status
    user.updated_at = datetime.now(UTC)
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserPublic.from_user(user)


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(current_user),
) -> MessageResponse:
    """Delete a user; cannot remove yourself or the last active admin."""
    if user_id == current.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Cannot delete your own account"},
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found"},
        )

    if user.role == "admin" and user.status == "active" and _count_active_admins(session) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Cannot delete the last active admin"},
        )

    session.delete(user)
    session.commit()
    return MessageResponse(message="User deleted")
