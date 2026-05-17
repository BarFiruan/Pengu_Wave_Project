"""Pydantic request/response models for the HTTP API.

Public schemas deliberately omit password_hash. Input models use
extra="forbid" where clients must not smuggle extra fields.
"""

import json
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Event, User

Role = Literal["admin", "analyst", "viewer"]
Status = Literal["active", "disabled"]
Severity = Literal["HIGH", "MEDIUM", "LOW"]


class LoginRequest(BaseModel):
    """POST /api/auth/login body; unknown fields rejected at validation time."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class UserPublic(BaseModel):
    """Safe user shape for JSON responses—never includes password or hash."""

    id: str
    email: str
    role: str
    status: str

    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        return cls(id=user.id, email=user.email, role=user.role, status=user.status)


class LoginResponse(BaseModel):
    """Login success: user profile only (session id travels in the cookie)."""

    user: UserPublic


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str


class CreateUserRequest(BaseModel):
    """POST /api/users body; role limited to Role literal."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    role: Role


class UpdateUserRequest(BaseModel):
    """PATCH body for /api/users/:id.

    extra="forbid" rejects unknown fields. This is the defence against
    mass-assignment: a client cannot send password_hash or any other field
    to overwrite it - the request fails 422 before any handler code runs.
    """

    model_config = ConfigDict(extra="forbid")

    role: Optional[Role] = None
    status: Optional[Status] = None


class EventPublic(BaseModel):
    """Event JSON uses camelCase to match the frontend and mock_events.json."""

    id: str
    timestamp: datetime
    severity: str
    title: str
    description: str
    assetHostname: str
    assetIp: str
    sourceIp: str
    tags: list[str]
    userId: Optional[str] = None

    @classmethod
    def from_event(cls, event: Event) -> "EventPublic":
        return cls(
            id=event.id,
            timestamp=event.timestamp,
            severity=event.severity,
            title=event.title,
            description=event.description,
            assetHostname=event.asset_hostname,
            assetIp=event.asset_ip,
            sourceIp=event.source_ip,
            tags=json.loads(event.tags_json or "[]"),
            userId=event.user_id,
        )


class MockEventSeed(BaseModel):
    """Validates rows from data/mock_events.json before inserting into SQLite."""

    id: str
    timestamp: datetime
    severity: Severity
    title: str
    description: str
    assetHostname: str
    assetIp: str
    sourceIp: str
    tags: list[str] = []
    userId: Optional[str] = None

    def to_db_event(self) -> Event:
        return Event(
            id=self.id,
            timestamp=self.timestamp,
            severity=self.severity,
            title=self.title,
            description=self.description,
            asset_hostname=self.assetHostname,
            asset_ip=self.assetIp,
            source_ip=self.sourceIp,
            tags_json=json.dumps(self.tags),
            user_id=self.userId,
        )
