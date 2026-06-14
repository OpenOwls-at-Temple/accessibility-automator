"""Authentication routes.

Mock (dev): POST /auth/login with an email establishes a signed-cookie session.
Azure (prod): the same endpoints would drive the OIDC redirect flow once wired.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.auth import session
from backend.app.auth.base import AuthProvider
from backend.app.auth.models import User
from backend.app.deps import get_auth_provider, get_current_user, get_settings, get_storage
from backend.app.schemas.models import LoginRequest
from backend.app.services.storage import StorageService
from backend.app.settings import Settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=User)
def login(
    body: LoginRequest,
    response: Response,
    provider: AuthProvider = Depends(get_auth_provider),
    settings: Settings = Depends(get_settings),
    storage: StorageService = Depends(get_storage),
) -> User:
    try:
        user = provider.authenticate(body.email)
    except (ValueError, NotImplementedError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    storage.ensure_workspace(user.username)
    token = session.issue(user.model_dump(), settings.session_secret)
    response.set_cookie(
        key=session.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.environment != "local",
    )
    return user


@router.get("/me", response_model=User)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(session.COOKIE_NAME)
    return {"ok": True}
