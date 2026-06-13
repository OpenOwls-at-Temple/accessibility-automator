"""Runtime settings read from the environment (see .env.example).

Secrets and deployment-specific values live in env vars; non-secret engine
behavior lives in ``config.yaml`` (loaded separately by the engine).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    auth_provider: str = "mock"  # "mock" | "azure"
    session_secret: str = "dev-secret-change-me"
    storage_dir: Path = field(default_factory=lambda: Path("./storage"))
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])
    environment: str = "local"

    # Azure AD / Temple SSO (production only)
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_tenant_id: str = ""
    azure_redirect_uri: str = ""


def load_settings(env: dict | None = None) -> Settings:
    env = env if env is not None else os.environ
    origins = [o.strip() for o in env.get("CORS_ORIGINS", "http://localhost:5173").split(",")]
    return Settings(
        auth_provider=env.get("AUTH_PROVIDER", "mock").lower(),
        session_secret=env.get("SESSION_SECRET", "dev-secret-change-me"),
        storage_dir=Path(env.get("STORAGE_DIR", "./storage")),
        cors_origins=[o for o in origins if o],
        environment=env.get("ENVIRONMENT", "local"),
        azure_client_id=env.get("AZURE_CLIENT_ID", ""),
        azure_client_secret=env.get("AZURE_CLIENT_SECRET", ""),
        azure_tenant_id=env.get("AZURE_TENANT_ID", ""),
        azure_redirect_uri=env.get("AZURE_REDIRECT_URI", ""),
    )
