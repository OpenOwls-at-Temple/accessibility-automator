"""Backend test fixtures: a TestClient backed by temp per-test storage, plus
helpers to log in, build a tiny PPTX, and poll a remediation job.
"""

from __future__ import annotations

import io
import time

import pytest
from fastapi.testclient import TestClient
from pptx import Presentation

from backend.app.main import create_app
from backend.app.settings import Settings
from remediator.config import load_config

API = "/api/v1"


@pytest.fixture
def app(tmp_path):
    settings = Settings(
        auth_provider="mock",
        session_secret="test-secret",
        storage_dir=tmp_path / "storage",
        cors_origins=["http://localhost:5173"],
        environment="local",
    )
    return create_app(settings=settings, config=load_config())


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def pptx_bytes() -> bytes:
    """A deck with no document title and an untitled slide (fails P1, P2)."""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.placeholders[1].text = "Mitochondria are the powerhouse of the cell."
    prs.core_properties.title = ""
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def login(client: TestClient, email: str = "prof@temple.edu") -> dict:
    resp = client.post(f"{API}/auth/login", json={"email": email})
    assert resp.status_code == 200, resp.text
    return resp.json()


def upload(client: TestClient, group: str, filename: str, data: bytes):
    return client.post(
        f"{API}/groups/{group}/files",
        files={"files": (filename, data, "application/octet-stream")},
    )


def wait_for_job(client: TestClient, job_id: str, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = client.get(f"{API}/jobs/{job_id}").json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(0.1)
    raise AssertionError(f"Job {job_id} did not finish in {timeout}s")
