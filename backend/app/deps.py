"""FastAPI dependencies — pull shared state off ``app.state`` and resolve the
current user from the signed session cookie.

Resolving the user from the cookie (never from a client-supplied path) is what
guarantees a user can only ever touch their own workspace.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from backend.app.auth import session
from backend.app.auth.base import AuthProvider
from backend.app.auth.models import User
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


def get_auth_provider(request: Request) -> AuthProvider:
    return request.app.state.auth_provider


def get_current_user(request: Request, settings: Settings = Depends(get_settings)) -> User:
    token = request.cookies.get(session.COOKIE_NAME)
    payload = session.verify(token, settings.session_secret) if token else None
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return User(username=payload["username"], email=payload["email"], name=payload["name"])
