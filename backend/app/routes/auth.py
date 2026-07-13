"""Authentication.

Sign-in = Google verifies *identity*, our allowlist decides *authorization*:

    POST /auth/login      Google ID token -> verify -> @domain check -> allowlist
                          lookup -> app JWT. Never auto-provisions.
    GET  /auth/me         the current user.
    POST /auth/dev-login  local-only shortcut that skips Google but still requires
                          a registered, active user (disabled outside ENVIRONMENT=local).
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, get_current_user
from backend.app.deps import get_settings, get_storage
from backend.app.models.base import utc_now
from backend.app.models.user import User
from backend.app.schemas.user import (
    DevLoginRequest,
    GoogleLoginRequest,
    TokenResponse,
    UserOut,
)
from backend.app.services.storage import StorageService
from backend.app.settings import Settings

router = APIRouter(prefix="/auth", tags=["auth"])

_GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def _lookup_active_user(db: Session, email: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not user.is_active:
        return None
    return user


def _issue_token(
    db: Session, user: User, settings: Settings, storage: StorageService
) -> TokenResponse:
    """Stamp the login, ensure the workspace, and mint an app JWT."""
    user.last_login_at = utc_now()
    db.commit()
    storage.ensure_workspace(user.username)
    return TokenResponse(access_token=create_access_token(user, settings.jwt_secret))


async def _verify_google_token(credential: str, settings: Settings) -> dict:
    """Verify a Google ID token via Google's tokeninfo endpoint; return its claims."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(_GOOGLE_TOKENINFO_URL, params={"id_token": credential})
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential"
        )
    claims = response.json()
    if claims.get("aud") != settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token audience mismatch"
        )
    return claims


@router.post("/login", response_model=TokenResponse)
async def login(
    body: GoogleLoginRequest,
    settings: Settings = Depends(get_settings),
    storage: StorageService = Depends(get_storage),
    db: Session = Depends(get_db),
) -> TokenResponse:
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SSO is not configured (GOOGLE_CLIENT_ID is missing)",
        )

    claims = await _verify_google_token(body.credential, settings)
    email = (claims.get("email") or "").strip().lower()
    if not email.endswith(f"@{settings.allowed_email_domain}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Sign-in is restricted to @{settings.allowed_email_domain} accounts",
        )

    # Identity verified; authorization is the admin-managed allowlist. Unknown or
    # inactive accounts get no access — we never auto-provision.
    user = _lookup_active_user(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not registered. Ask an administrator to add you.",
        )
    if not user.name and claims.get("name"):
        user.name = claims["name"]
    return _issue_token(db, user, settings, storage)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/dev-login", response_model=TokenResponse)
def dev_login(
    body: DevLoginRequest,
    settings: Settings = Depends(get_settings),
    storage: StorageService = Depends(get_storage),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Local-development login that skips Google. 404 outside ENVIRONMENT=local."""
    if settings.environment != "local":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    user = _lookup_active_user(db, body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not registered or inactive",
        )
    return _issue_token(db, user, settings, storage)
