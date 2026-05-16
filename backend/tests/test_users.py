
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.conftest import login


def test_admin_can_list_users(client: TestClient, admin_user, analyst_user):
    login(client, admin_user.email, "adminpass123")
    response = client.get("/api/users")
    assert response.status_code == 200
    emails = {u["email"] for u in response.json()}
    assert admin_user.email in emails
    assert analyst_user.email in emails
    # UserPublic must never leak password or hash fields in list responses.
    assert "password" not in response.text
    assert "password_hash" not in response.text


def test_admin_can_create_user(client: TestClient, admin_user):
    login(client, admin_user.email, "adminpass123")
    response = client.post(
        "/api/users",
        json={"email": "newuser@test.io", "password": "newpass1234", "role": "analyst"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@test.io"
    assert "password" not in response.text


def test_analyst_forbidden(client: TestClient, analyst_user):
    login(client, analyst_user.email, "analystpass123")
    for method, path, kwargs in [
        ("get", "/api/users", {}),
        (
            "post",
            "/api/users",
            {"json": {"email": "x@test.io", "password": "longpass12", "role": "viewer"}},
        ),
        ("patch", f"/api/users/{analyst_user.id}", {"json": {"role": "viewer"}}),
        ("delete", f"/api/users/{analyst_user.id}", {}),
    ]:
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 403, (method, path, response.text)


def test_viewer_forbidden(client: TestClient, viewer_user, admin_user):
    login(client, viewer_user.email, "viewerpass123")
    response = client.get("/api/users")
    assert response.status_code == 403


def test_anon_unauthorized(client: TestClient):
    response = client.get("/api/users")
    assert response.status_code == 401


def test_mass_assignment_rejected(client: TestClient, admin_user, analyst_user):
    login(client, admin_user.email, "adminpass123")
    response = client.patch(
        f"/api/users/{analyst_user.id}",
        json={"role": "viewer", "password_hash": "hacked"},
    )
    assert response.status_code == 422


def test_duplicate_email(client: TestClient, admin_user, analyst_user):
    login(client, admin_user.email, "adminpass123")
    response = client.post(
        "/api/users",
        json={"email": analyst_user.email, "password": "anotherpass1", "role": "viewer"},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Email already in use"


def test_cannot_delete_self(client: TestClient, admin_user):
    login(client, admin_user.email, "adminpass123")
    response = client.delete(f"/api/users/{admin_user.id}")
    assert response.status_code == 400
    assert "own account" in response.json()["error"]


def test_last_admin_demotion_blocked(client: TestClient, session: Session, admin_user):
    login(client, admin_user.email, "adminpass123")
    response = client.patch(
        f"/api/users/{admin_user.id}",
        json={"role": "analyst"},
    )
    assert response.status_code == 400
    assert "last active admin" in response.json()["error"]
