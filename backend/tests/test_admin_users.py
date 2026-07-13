"""Admin user management (the invite mechanism)."""

from backend.tests.conftest import API, login


def test_admin_can_invite_list_and_deactivate(client, db_session):
    login(client, db_session, "admin@temple.edu", is_admin=True)

    # Invite a new Temple user.
    created = client.post(f"{API}/admin/users", json={"email": "New.Prof@temple.edu"})
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "new.prof@temple.edu"
    assert body["is_active"] is True

    # They appear in the list.
    listed = client.get(f"{API}/admin/users").json()
    emails = {u["email"] for u in listed}
    assert {"admin@temple.edu", "new.prof@temple.edu"} <= emails

    # Deactivate them.
    patched = client.patch(f"{API}/admin/users/{body['id']}", json={"is_active": False})
    assert patched.status_code == 200
    assert patched.json()["is_active"] is False


def test_duplicate_invite_conflicts(client, db_session):
    login(client, db_session, "admin@temple.edu", is_admin=True)
    client.post(f"{API}/admin/users", json={"email": "dup@temple.edu"})
    again = client.post(f"{API}/admin/users", json={"email": "dup@temple.edu"})
    assert again.status_code == 409


def test_non_admin_cannot_manage_users(client, db_session):
    login(client, db_session, "prof@temple.edu", is_admin=False)
    assert client.get(f"{API}/admin/users").status_code == 403
    assert client.post(f"{API}/admin/users", json={"email": "x@temple.edu"}).status_code == 403


def test_invited_user_can_then_sign_in(client, db_session):
    login(client, db_session, "admin@temple.edu", is_admin=True)
    client.post(f"{API}/admin/users", json={"email": "invitee@temple.edu"})
    # A fresh (unauthenticated) client can dev-login as the invited user.
    from fastapi.testclient import TestClient

    fresh = TestClient(client.app)
    resp = fresh.post(f"{API}/auth/dev-login", json={"email": "invitee@temple.edu"})
    assert resp.status_code == 200
