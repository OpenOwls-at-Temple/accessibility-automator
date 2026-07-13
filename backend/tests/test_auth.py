"""Auth: Google verification + admin allowlist + JWT bearer + dev-login."""

from fastapi.testclient import TestClient

import backend.app.routes.auth as auth_route
from backend.app.core.database import get_db
from backend.app.main import create_app
from backend.app.settings import Settings
from backend.tests.conftest import API, login, register
from remediator.config import load_config


def test_health_is_open(client):
    assert client.get(f"{API}/health").json()["status"] == "ok"


def test_me_requires_authentication(client):
    assert client.get(f"{API}/auth/me").status_code == 401


def test_dev_login_and_me_work(client, db_session):
    login(client, db_session, "Jane.Doe@temple.edu")
    me = client.get(f"{API}/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "jane.doe@temple.edu"


def test_dev_login_rejects_unregistered_email(client, db_session):
    # Nobody registered -> even a valid Temple email cannot log in.
    resp = client.post(f"{API}/auth/dev-login", json={"email": "ghost@temple.edu"})
    assert resp.status_code == 401


def test_dev_login_rejects_inactive_user(client, db_session):
    register(db_session, "gone@temple.edu", is_active=False)
    resp = client.post(f"{API}/auth/dev-login", json={"email": "gone@temple.edu"})
    assert resp.status_code == 401


def test_dev_login_disabled_outside_local(tmp_path, db_session):
    prod = create_app(
        settings=Settings(
            google_client_id="x",
            environment="production",
            storage_dir=tmp_path / "s",
        ),
        config=load_config(),
    )
    prod.dependency_overrides[get_db] = lambda: iter([db_session])
    register(db_session, "prof@temple.edu")
    client = TestClient(prod)
    assert (
        client.post(f"{API}/auth/dev-login", json={"email": "prof@temple.edu"}).status_code == 404
    )


def test_google_login_unconfigured_returns_503(tmp_path, db_session):
    app = create_app(
        settings=Settings(google_client_id="", storage_dir=tmp_path / "s"),
        config=load_config(),
    )
    app.dependency_overrides[get_db] = lambda: iter([db_session])
    resp = TestClient(app).post(f"{API}/auth/login", json={"credential": "tok"})
    assert resp.status_code == 503


def test_google_login_registered_temple_user_ok(client, db_session, monkeypatch):
    register(db_session, "prof@temple.edu")

    async def fake_verify(credential, settings):
        return {"email": "prof@temple.edu", "aud": settings.google_client_id, "name": "Prof"}

    monkeypatch.setattr(auth_route, "_verify_google_token", fake_verify)
    resp = client.post(f"{API}/auth/login", json={"credential": "tok"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_google_login_rejects_non_temple_domain(client, db_session, monkeypatch):
    async def fake_verify(credential, settings):
        return {"email": "someone@gmail.com", "aud": settings.google_client_id}

    monkeypatch.setattr(auth_route, "_verify_google_token", fake_verify)
    resp = client.post(f"{API}/auth/login", json={"credential": "tok"})
    assert resp.status_code == 403


def test_google_login_rejects_unregistered_temple_user(client, db_session, monkeypatch):
    async def fake_verify(credential, settings):
        return {"email": "student@temple.edu", "aud": settings.google_client_id}

    monkeypatch.setattr(auth_route, "_verify_google_token", fake_verify)
    resp = client.post(f"{API}/auth/login", json={"credential": "tok"})
    assert resp.status_code == 403
    assert "not registered" in resp.json()["detail"].lower()
