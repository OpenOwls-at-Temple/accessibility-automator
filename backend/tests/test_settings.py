from backend.tests.conftest import API, login, upload, wait_for_job


def test_default_suffix_is_a11y(client, db_session):
    login(client, db_session)
    assert client.get(f"{API}/settings").json() == {"filename_suffix": "a11y"}


def test_update_suffix(client, db_session):
    login(client, db_session)
    resp = client.put(f"{API}/settings", json={"filename_suffix": "fixed"})
    assert resp.status_code == 200 and resp.json()["filename_suffix"] == "fixed"
    # Persisted across reads.
    assert client.get(f"{API}/settings").json()["filename_suffix"] == "fixed"


def test_invalid_suffix_is_rejected(client, db_session):
    login(client, db_session)
    for bad in ["", "has space", "a/b", ".."]:
        assert client.put(f"{API}/settings", json={"filename_suffix": bad}).status_code == 400
    # A rejected update leaves the previous value intact.
    assert client.get(f"{API}/settings").json()["filename_suffix"] == "a11y"


def test_output_uses_configured_suffix(client, db_session, pptx_bytes):
    login(client, db_session)
    client.put(f"{API}/settings", json={"filename_suffix": "remediated"})
    upload(client, "CIS4526", "lecture1.pptx", pptx_bytes)
    wait_for_job(client, client.post(f"{API}/groups/CIS4526/remediate", json={}).json()["job_id"])

    out = client.get(f"{API}/groups/CIS4526/files/lecture1.pptx/download?kind=output")
    assert out.status_code == 200
    assert "lecture1_remediated.pptx" in out.headers["content-disposition"]


def test_changing_suffix_keeps_old_outputs_downloadable(client, db_session, pptx_bytes):
    """The whole point of storing the output name: a later suffix change must not
    orphan a file already remediated under the old suffix."""
    login(client, db_session)
    upload(client, "CIS4526", "lecture1.pptx", pptx_bytes)
    wait_for_job(client, client.post(f"{API}/groups/CIS4526/remediate", json={}).json()["job_id"])

    # Now change the suffix — the already-remediated file keeps its original name.
    client.put(f"{API}/settings", json={"filename_suffix": "v2"})

    detail = {f["name"]: f for f in client.get(f"{API}/groups/CIS4526").json()["files"]}
    assert detail["lecture1.pptx"]["has_output"] is True

    out = client.get(f"{API}/groups/CIS4526/files/lecture1.pptx/download?kind=output")
    assert out.status_code == 200
    assert "lecture1_a11y.pptx" in out.headers["content-disposition"]  # not _v2

    # The report for the old output still resolves too.
    assert client.get(f"{API}/groups/CIS4526/files/lecture1.pptx/report").status_code == 200
