from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import get_settings
from app.models import Session as DbSession
from tests.conftest import create_user, login

settings = get_settings()


def test_login_success(client: TestClient, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"email": admin_user.email, "password": "adminpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" not in data
    assert data["user"]["email"] == admin_user.email
    assert settings.cookie_name in response.cookies


def test_login_wrong_password(client: TestClient, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"email": admin_user.email, "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid email or password"}


def test_login_disabled_user(client: TestClient, session: Session):
    user = create_user(
        session,
        email="disabled@test.io",
        password="disabledpass123",
        role="viewer",
        status="disabled",
    )
    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "disabledpass123"},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid email or password"}


def test_me_without_cookie(client: TestClient):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"error": "Authentication required"}


def test_me_with_valid_session(client: TestClient, admin_user):
    login(client, admin_user.email, "adminpass123")
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == admin_user.email
    assert "password" not in response.text


def test_expired_session(client: TestClient, session: Session, admin_user):
    login(client, admin_user.email, "adminpass123")
    sid = client.cookies.get(settings.cookie_name)
    db_session = session.exec(select(DbSession).where(DbSession.id == sid)).first()
    assert db_session is not None
    db_session.expires_at = datetime.now(UTC) - timedelta(hours=1)
    session.add(db_session)
    session.commit()

    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_logout_invalidates_session(client: TestClient, session: Session, admin_user):
    login(client, admin_user.email, "adminpass123")
    sid = client.cookies.get(settings.cookie_name)
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert session.get(DbSession, sid) is None

    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_login_rate_limit(client: TestClient, admin_user):
    from app.limiter import limiter

    limiter.enabled = True
    for _ in range(10):
        client.post(
            "/api/auth/login",
            json={"email": admin_user.email, "password": "wrong"},
        )
    response = client.post(
        "/api/auth/login",
        json={"email": admin_user.email, "password": "wrong"},
    )
    assert response.status_code == 429
    limiter.enabled = False
