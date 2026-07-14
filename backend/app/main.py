"""FastAPI application factory.

    uvicorn backend.app.main:app --reload

Shared state (settings, engine config, storage, job manager) lives on
``app.state`` so it is easy to override in tests via ``create_app``. Auth is
DB-backed (users allowlist); the schema is created by Alembic, not here.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # always finds .env at repo root

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes import auth, files, groups, jobs, reports, users
from backend.app.routes import config as config_route
from backend.app.routes import settings as settings_route
from backend.app.services.jobs import JobManager
from backend.app.services.storage import StorageService
from backend.app.settings import Settings, load_settings
from remediator.config import Config, load_config

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None, config: Config | None = None) -> FastAPI:
    settings = settings or load_settings()
    config = config or load_config()

    app = FastAPI(title="Accessibility Automator", version="0.1.0")
    app.state.settings = settings
    app.state.config = config
    app.state.storage = StorageService(settings.storage_dir)
    app.state.jobs = JobManager(app.state.storage, config)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Let the browser read the download filename (``*_a11y.<ext>``) cross-origin;
        # without this the frontend can't see Content-Disposition and falls back to
        # the original name.
        expose_headers=["Content-Disposition"],
    )

    api = APIRouter(prefix=API_PREFIX)
    for module in (auth, users, groups, files, reports, jobs, settings_route, config_route):
        api.include_router(module.router)

    @api.get("/health")
    def health() -> dict:
        return {"status": "ok", "environment": settings.environment}

    app.include_router(api)
    return app


app = create_app()
