from backend.tests.conftest import API, login, upload, wait_for_job


def test_full_remediation_flow(client, pptx_bytes):
    login(client)
    upload(client, "CIS4526", "lecture1.pptx", pptx_bytes)

    # Kick off remediation -> background job.
    start = client.post(f"{API}/groups/CIS4526/remediate", json={})
    assert start.status_code == 200
    job_id = start.json()["job_id"]

    done = wait_for_job(client, job_id)
    assert done["status"] == "done"
    assert done["files_done"] == done["files_total"] == 1

    # Scores are recorded and the file is complete.
    detail = client.get(f"{API}/groups/CIS4526").json()
    entry = detail["files"][0]
    assert entry["status"] == "complete"
    assert entry["post_fix_score"] >= entry["pre_fix_score"]

    # Output is downloadable and is a real, larger-than-zero file.
    out = client.get(f"{API}/groups/CIS4526/files/lecture1.pptx/download?kind=output")
    assert out.status_code == 200
    assert "lecture1_a11y.pptx" in out.headers["content-disposition"]
    assert len(out.content) > 0

    # The JSON report exists and has the two-score breakdown.
    report = client.get(f"{API}/groups/CIS4526/files/lecture1.pptx/report").json()
    assert "scores" in report
    assert report["scores"]["post_fix_checker_passing"]["score"] >= 0


def test_signoff_acknowledges_a_placeholder(client, pptx_bytes):
    login(client)
    upload(client, "CIS4526", "lecture1.pptx", pptx_bytes)
    job_id = client.post(f"{API}/groups/CIS4526/remediate", json={}).json()["job_id"]
    wait_for_job(client, job_id)

    # No LLM configured in tests -> the untitled slide (P2) becomes a placeholder.
    config_meta = client.get(f"{API}/groups/CIS4526/files/lecture1.pptx/report").json()
    placeholder_checks = [
        f["check_id"] for f in config_meta["fixes"] if f["action"] == "placeholder"
    ]
    assert "P2" in placeholder_checks

    ok = client.post(
        f"{API}/groups/CIS4526/files/lecture1.pptx/signoff",
        json={"check_id": "P2", "note": "Reviewed by instructor"},
    )
    assert ok.status_code == 200


def test_remediate_unknown_group_is_404(client):
    login(client)
    assert client.post(f"{API}/groups/NOPE/remediate", json={}).status_code == 404


def test_job_belongs_to_its_owner(app, pptx_bytes):
    from fastapi.testclient import TestClient

    alice = TestClient(app)
    bob = TestClient(app)
    login(alice, "alice@temple.edu")
    login(bob, "bob@temple.edu")

    upload(alice, "CIS4526", "lecture1.pptx", pptx_bytes)
    job_id = alice.post(f"{API}/groups/CIS4526/remediate", json={}).json()["job_id"]

    # Bob cannot see Alice's job.
    assert bob.get(f"{API}/jobs/{job_id}").status_code == 404
