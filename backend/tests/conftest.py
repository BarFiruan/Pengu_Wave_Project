import os
import uuid
from collections.abc import Generator

os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.config import get_settings
from app.db import get_session
from app.main import create_app
from app.models import User
from app.security import hash_password

get_settings.cache_clear()
settings = get_settings()


@pytest.fixture(autouse=True)
def disable_rate_limit():
    from app.limiter import limiter

    limiter.enabled = False
    yield
    limiter.enabled = False


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    import app.db as db_module

    test_engine = session.get_bind()
    db_module.engine = test_engine

    def get_session_override() -> Generator[Session, None, None]:
        yield session

    app = create_app()
    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def create_user(
    session: Session,
    *,
    email: str,
    password: str,
    role: str = "analyst",
    status: str = "active",
) -> User:
    user = User(
        id=uuid.uuid4().hex,
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
        status=status,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def admin_user(session: Session) -> User:
    return create_user(session, email="admin@test.io", password="adminpass123", role="admin")


@pytest.fixture
def analyst_user(session: Session) -> User:
    return create_user(
        session, email="analyst@test.io", password="analystpass123", role="analyst"
    )


@pytest.fixture
def viewer_user(session: Session) -> User:
    return create_user(
        session, email="viewer@test.io", password="viewerpass123", role="viewer"
    )


def login(client: TestClient, email: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
