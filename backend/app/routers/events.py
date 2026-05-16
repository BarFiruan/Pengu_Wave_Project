from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, or_, select

from app.db import get_session
from app.deps import current_user
from app.models import Event, User
from app.schemas import EventPublic

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventPublic])
def list_events(
    severity: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    _user: User = Depends(current_user),
) -> list[EventPublic]:
    statement = select(Event).order_by(Event.timestamp.desc())
    if severity:
        statement = statement.where(Event.severity == severity.upper())
    if search:
        term = f"%{search}%"
        statement = statement.where(
            or_(
                Event.title.ilike(term),
                Event.description.ilike(term),
                Event.asset_hostname.ilike(term),
            )
        )
    statement = statement.offset(offset).limit(limit)
    events = session.exec(statement).all()
    return [EventPublic.from_event(e) for e in events]


@router.get("/{event_id}", response_model=EventPublic)
def get_event(
    event_id: str,
    session: Session = Depends(get_session),
    _user: User = Depends(current_user),
) -> EventPublic:
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Event not found"},
        )
    return EventPublic.from_event(event)
