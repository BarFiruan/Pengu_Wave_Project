import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Event
from tests.conftest import login


def seed_event(session: Session, **kwargs) -> Event:
    event = Event(
        id=kwargs.get("id", "evt-test-1"),
        timestamp=kwargs.get("timestamp", datetime.now(UTC)),
        severity=kwargs.get("severity", "HIGH"),
        title=kwargs.get("title", "Test event"),
        description=kwargs.get("description", "Something suspicious"),
        asset_hostname=kwargs.get("asset_hostname", "host.internal"),
        asset_ip=kwargs.get("asset_ip", "10.0.0.1"),
        source_ip=kwargs.get("source_ip", "10.0.0.2"),
        tags_json=json.dumps(kwargs.get("tags", ["test"])),
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def test_events_require_auth(client: TestClient):
    response = client.get("/api/events")
    assert response.status_code == 401


def test_authenticated_list(client: TestClient, admin_user, session: Session):
    seed_event(session, id="evt-1", title="Alpha breach")
    seed_event(session, id="evt-2", title="Beta scan", severity="LOW")
    login(client, admin_user.email, "adminpass123")

    response = client.get("/api/events")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_events_filter_severity(client: TestClient, admin_user, session: Session):
    seed_event(session, id="evt-high", severity="HIGH")
    seed_event(session, id="evt-low", severity="LOW", title="Low priority")
    login(client, admin_user.email, "adminpass123")

    response = client.get("/api/events", params={"severity": "LOW"})
    assert response.status_code == 200
    assert all(e["severity"] == "LOW" for e in response.json())


def test_events_search(client: TestClient, admin_user, session: Session):
    seed_event(session, id="evt-search", title="UniqueKeywordEvent")
    login(client, admin_user.email, "adminpass123")

    response = client.get("/api/events", params={"search": "UniqueKeyword"})
    assert response.status_code == 200
    assert any("UniqueKeyword" in e["title"] for e in response.json())


def test_event_not_found(client: TestClient, admin_user):
    login(client, admin_user.email, "adminpass123")
    response = client.get("/api/events/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"] == "Event not found"
