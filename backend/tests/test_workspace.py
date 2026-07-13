from backend.tests.conftest import API, login, upload


def test_new_user_has_no_groups(client, db_session):
    login(client, db_session)
    assert client.get(f"{API}/groups").json() == []


def test_upload_creates_group_and_lists_file(client, db_session, pptx_bytes):
    login(client, db_session)
    resp = upload(client, "CIS4526", "lecture1.pptx", pptx_bytes)
    assert resp.status_code == 200
    assert resp.json()["saved"] == ["lecture1.pptx"]

    groups = client.get(f"{API}/groups").json()
    assert groups == [{"name": "CIS4526", "file_count": 1}]

    detail = client.get(f"{API}/groups/CIS4526").json()
    assert detail["files"][0]["name"] == "lecture1.pptx"
    assert detail["files"][0]["status"] == "uploaded"


def test_upload_rejects_unsupported_type(client, db_session):
    login(client, db_session)
    resp = upload(client, "CIS4526", "notes.txt", b"hello")
    assert resp.status_code == 400


def test_upload_rejects_path_traversal_filename(client, db_session, pptx_bytes):
    login(client, db_session)
    resp = upload(client, "CIS4526", "../evil.pptx", pptx_bytes)
    assert resp.status_code == 400


def test_upload_allows_filename_with_spaces(client, db_session, pptx_bytes):
    login(client, db_session)
    name = "lecture 1 intro.pptx"
    resp = upload(client, "CIS4526", name, pptx_bytes)
    assert resp.status_code == 200
    assert resp.json()["saved"] == [name]

    detail = client.get(f"{API}/groups/CIS4526").json()
    assert detail["files"][0]["name"] == name

    # The spaced name round-trips through a URL-encoded download path.
    from urllib.parse import quote

    dl = client.get(f"{API}/groups/CIS4526/files/{quote(name)}/download?kind=input")
    assert dl.status_code == 200


def test_missing_group_is_404(client, db_session):
    login(client, db_session)
    assert client.get(f"{API}/groups/NOPE").status_code == 404


def test_user_cannot_access_another_users_workspace(app, db_session, pptx_bytes):
    from fastapi.testclient import TestClient

    alice = TestClient(app)
    bob = TestClient(app)
    login(alice, db_session, "alice@temple.edu")
    login(bob, db_session, "bob@temple.edu")

    upload(alice, "CIS4526", "lecture1.pptx", pptx_bytes)

    # Bob has his own empty workspace and cannot see Alice's file.
    assert bob.get(f"{API}/groups").json() == []
    assert (
        bob.get(f"{API}/groups/CIS4526/files/lecture1.pptx/download?kind=input").status_code == 404
    )
