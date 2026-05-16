"""First-run database seeding: admin user and mock security events.

Runs on app startup when tables are empty. Skipped entirely when
ENVIRONMENT=test so pytest fixtures control their own data.
"""

import json
import secrets
import uuid

import structlog
from sqlmodel import Session, select

from app.config import get_settings
from app.models import Event, User
from app.schemas import MockEventSeed
from app.security import hash_password

logger = structlog.get_logger()
settings = get_settings()


def seed_database(session: Session) -> None:
    """Populate admin and events if this is a fresh database (not in tests)."""
    if settings.environment == "test":
        return
    seed_admin_user(session)
    seed_events(session)


def seed_admin_user(session: Session) -> None:
    """Create the initial admin if the user table is empty.

  Password comes from ADMIN_BOOTSTRAP_PASSWORD or a one-time random value
  printed to stdout so reviewers can log in without committing a secret.
  """
    existing = session.exec(select(User)).first()
    if existing:
        return

    password = settings.admin_bootstrap_password
    if not password:
        password = secrets.token_urlsafe(16)
        print(
            f"\n*** Admin bootstrap password (save this): {password} ***\n"
            f"    Email: {settings.admin_email.lower()}\n"
        )

    admin = User(
        id=uuid.uuid4().hex,
        email=settings.admin_email.lower(),
        password_hash=hash_password(password),
        role="admin",
        status="active",
    )
    session.add(admin)
    session.commit()
    logger.info("seeded_admin_user", email=admin.email)


def seed_events(session: Session) -> None:
    """Load data/mock_events.json into the event table when empty."""
    existing = session.exec(select(Event)).first()
    if existing:
        return

    path = settings.mock_events_path
    if not path.exists():
        logger.warning("mock_events_missing", path=str(path))
        return

    raw = json.loads(path.read_text(encoding="utf-8"))
    events = [MockEventSeed.model_validate(item).to_db_event() for item in raw]
    session.add_all(events)
    session.commit()
    logger.info("seeded_events", count=len(events))
