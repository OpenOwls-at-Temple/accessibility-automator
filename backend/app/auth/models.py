"""The authenticated user."""

from __future__ import annotations

from pydantic import BaseModel


class User(BaseModel):
    username: str  # workspace key — the email local-part, sanitized
    email: str
    name: str
