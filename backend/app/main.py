"""FastAPI application factory.

    uvicorn backend.app.main:app --reload

Shared state (settings, engine config, storage, job manager, auth provider)
lives on ``app.state`` so it is easy to override in tests via ``create_app``.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")  # always finds .env at repo root

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.auth.azure_oidc import AzureOIDCProvider
from backend.app.auth.base import AuthProvider
from backend.app.auth.mock import MockAuthProvider
from backend.app.routes import auth, files, groups, jobs, reports
from backend.app.routes import config as config_route
from backend.app.services.jobs import JobManager
from backend.app.services.storage import StorageService
from backend.app.settings import Settings, load_settings
from remediator.config import Config, load_config

API_PREFIX = "/api/v1"


def _make_auth_provider(settings: Settings) -> AuthProvider:
    if settings.auth_provider == "azure":
        return AzureOIDCProvider(settings)
    return MockAuthProvider()


def create_app(settings: Settings | None = None, config: Config | None = None) -> FastAPI:
    settings = settings or load_settings()
    config = config or load_config()

    app = FastAPI(title="Accessibility Automator", version="0.1.0")
    app.state.settings = settings
    app.state.config = config
    app.state.storage = StorageService(settings.storage_dir)
    app.state.jobs = JobManager(app.state.storage, config)
    app.state.auth_provider = _make_auth_provider(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix=API_PREFIX)
    for module in (auth, groups, files, reports, jobs, config_route):
        api.include_router(module.router)
    app.include_router(api)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
