"""FastAPI dependencies — pull shared state off ``app.state`` and resolve the
current user from the JWT bearer token.

Resolving the user from the token (then keying storage by the *authenticated*
email, never a client-supplied path) is what guarantees a user can only ever
touch their own workspace. ``get_current_user`` / ``get_current_admin`` live in
``core.security`` and are re-exported here for convenience.
"""

from __future__ import annotations

from fastapi import Request

from backend.app.core.security import get_current_admin, get_current_user  # noqa: F401
from backend.app.services.jobs import JobManager
from backend.app.services.storage import StorageService
from backend.app.settings import Settings
from remediator.config import Config


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_config(request: Request) -> Config:
    return request.app.state.config


def get_storage(request: Request) -> StorageService:
    return request.app.state.storage


def get_jobs(request: Request) -> JobManager:
    return request.app.state.jobs
