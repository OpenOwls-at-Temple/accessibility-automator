"""Auth + user-management request/response shapes."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    affiliation: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None


class UserCreate(BaseModel):
    email: str
    name: str = ""
    affiliation: str = ""
    is_admin: bool = False

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("must be a valid email address")
        return value


class UserUpdate(BaseModel):
    name: str | None = None
    affiliation: str | None = None
    is_admin: bool | None = None
    is_active: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token obtained by the frontend via GIS


class DevLoginRequest(BaseModel):
    email: str
