"""Runtime settings read from the environment (see .env.example).

Secrets and deployment-specific values live in env vars; non-secret engine
behavior lives in ``config.yaml`` (loaded separately by the engine).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load a local .env once at import (no-op if absent). Real environment variables
# — e.g. Render's — always take precedence, since load_dotenv does not override.
load_dotenv()


@dataclass
class Settings:
    # Sign-in: Google Identity Services + an admin-managed allowlist (see
    # ai_specs/architecture-planning.md). A verified Google ID token whose email
    # ends in ``allowed_email_domain`` AND exists in the users table gets in.
    google_client_id: str = ""
    allowed_email_domain: str = "temple.edu"
    jwt_secret: str = "dev-only-secret-change-me"

    database_url: str = "sqlite:///./a11y.db"
    storage_dir: Path = field(default_factory=lambda: Path("./storage"))
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])
    environment: str = "local"


def load_settings(env: dict | None = None) -> Settings:
    env = env if env is not None else os.environ
    frontend_url = env.get("FRONTEND_URL", "http://localhost:5173")
    origins = [o.strip() for o in env.get("CORS_ORIGINS", frontend_url).split(",")]
    return Settings(
        google_client_id=env.get("GOOGLE_CLIENT_ID", ""),
        allowed_email_domain=env.get("ALLOWED_EMAIL_DOMAIN", "temple.edu").lower(),
        jwt_secret=env.get("JWT_SECRET", "dev-only-secret-change-me"),
        database_url=env.get("DATABASE_URL", "sqlite:///./a11y.db"),
        storage_dir=Path(env.get("STORAGE_DIR", "./storage")),
        frontend_url=frontend_url,
        cors_origins=[o for o in origins if o],
        environment=env.get("ENVIRONMENT", "local").lower(),
    )
