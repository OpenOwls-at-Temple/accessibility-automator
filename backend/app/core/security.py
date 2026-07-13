"""App session tokens (JWT bearer) + the current-user dependencies.

Google verifies *identity* (see routes/auth.py); this module mints and checks
the app's own short-lived JWT, and resolves it to an active allowlisted user.
The signing secret is read per-request from ``app.state.settings`` so tests can
override it without touching module state.
"""

from __future__ import annotations

from datetime import timedelta

from authlib.jose import JoseError, jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import utc_now
from backend.app.models.user import User

ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=12)

_bearer = HTTPBearer(auto_error=False)


def create_access_token(user: User, jwt_secret: str, ttl: timedelta = TOKEN_TTL) -> str:
    now = utc_now()
    payload = {
        "sub": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    token = jwt.encode({"alg": ALGORITHM}, payload, jwt_secret)
    return token.decode() if isinstance(token, bytes) else token


def decode_access_token(token: str, jwt_secret: str) -> dict:
    claims = jwt.decode(token, jwt_secret)
    claims.validate()  # raises on expired/invalid claims
    return dict(claims)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        claims = decode_access_token(credentials.credentials, request.app.state.settings.jwt_secret)
    except JoseError:
        raise unauthorized
    user = db.get(User, claims.get("sub"))
    if user is None or not user.is_active:
        raise unauthorized
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
