"""The auth provider interface + username derivation."""

from __future__ import annotations

import abc
import re

from backend.app.auth.models import User

_UNSAFE = re.compile(r"[^a-z0-9._-]+")


def username_from_email(email: str) -> str:
    """Derive a filesystem-safe workspace key from an email local-part."""
    local = email.strip().lower().split("@", 1)[0]
    cleaned = _UNSAFE.sub("", local)
    return cleaned or "user"


class AuthProvider(abc.ABC):
    """Resolves a sign-in into a :class:`User`."""

    @abc.abstractmethod
    def authenticate(self, email: str | None = None) -> User:
        """Return the authenticated user, or raise on failure."""
