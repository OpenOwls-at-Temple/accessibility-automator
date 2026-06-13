from backend.tests.conftest import API, login, upload


def test_new_user_has_no_groups(client):
    login(client)
    assert client.get(f"{API}/groups").json() == []


def test_upload_creates_group_and_lists_file(client, pptx_bytes):
    login(client)
    resp = upload(client, "CIS4526", "lecture1.pptx", pptx_bytes)
    assert resp.status_code == 200
    assert resp.json()["saved"] == ["lecture1.pptx"]

    groups = client.get(f"{API}/groups").json()
    assert groups == [{"name": "CIS4526", "file_count": 1}]

    detail = client.get(f"{API}/groups/CIS4526").json()
    assert detail["files"][0]["name"] == "lecture1.pptx"
    assert detail["files"][0]["status"] == "uploaded"


def test_upload_rejects_unsupported_type(client):
    login(client)
    resp = upload(client, "CIS4526", "notes.txt", b"hello")
    assert resp.status_code == 400


def test_upload_rejects_path_traversal_filename(client, pptx_bytes):
    login(client)
    resp = upload(client, "CIS4526", "../evil.pptx", pptx_bytes)
    assert resp.status_code == 400


def test_missing_group_is_404(client):
    login(client)
    assert client.get(f"{API}/groups/NOPE").status_code == 404


def test_user_cannot_access_another_users_workspace(app, pptx_bytes):
    from fastapi.testclient import TestClient

    alice = TestClient(app)
    bob = TestClient(app)
    login(alice, "alice@temple.edu")
    login(bob, "bob@temple.edu")

    upload(alice, "CIS4526", "lecture1.pptx", pptx_bytes)

    # Bob sees nothing of Alice's, and cannot reach her group or files.
    assert bob.get(f"{API}/groups").json() == []
    assert bob.get(f"{API}/groups/CIS4526").status_code == 404
    assert (
        bob.get(f"{API}/groups/CIS4526/files/lecture1.pptx/download?kind=input").status_code == 404
    )
