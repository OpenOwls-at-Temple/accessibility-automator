from backend.tests.conftest import API, login


def test_health_is_open(client):
    assert client.get("/health").json()["status"] == "ok"


def test_me_requires_authentication(client):
    assert client.get(f"{API}/auth/me").status_code == 401


def test_login_sets_session_and_me_works(client):
    user = login(client, "Jane.Doe@temple.edu")
    assert user["username"] == "jane.doe"
    assert user["email"] == "jane.doe@temple.edu"

    me = client.get(f"{API}/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "jane.doe"


def test_logout_clears_session(client):
    login(client)
    assert client.get(f"{API}/auth/me").status_code == 200
    client.post(f"{API}/auth/logout")
    assert client.get(f"{API}/auth/me").status_code == 401


def test_login_rejects_bad_email(client):
    assert client.post(f"{API}/auth/login", json={"email": "not-an-email"}).status_code == 400


def test_tampered_cookie_is_rejected(client):
    login(client)
    # client.cookies.set() adds a *second* cookie under a different jar domain
    # rather than overwriting the first, so both get sent and the server's
    # cookie parser picks the still-valid one - silently passing this test
    # without ever exercising the tamper path. Clear the jar first so only
    # the tampered value is sent.
    client.cookies.clear()
    client.cookies.set("a11y_session", "garbage.signature")
    assert client.get(f"{API}/auth/me").status_code == 401
