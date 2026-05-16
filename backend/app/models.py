from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str
    status: str = "active"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Session(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)


class Event(SQLModel, table=True):
    id: str = Field(primary_key=True)
    timestamp: datetime = Field(index=True)
    severity: str = Field(index=True)
    title: str
    description: str
    asset_hostname: str
    asset_ip: str
    source_ip: str
    tags_json: str = "[]"
    user_id: Optional[str] = Field(default=None, foreign_key="user.id")
