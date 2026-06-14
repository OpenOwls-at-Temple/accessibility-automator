"""Mock auth for local development: enter an email, get the matching workspace.

No external dependency — lets the whole app be built and tested before real
Temple SSO is wired in.
"""

from __future__ import annotations

from backend.app.auth.base import AuthProvider, username_from_email
from backend.app.auth.models import User


class MockAuthProvider(AuthProvider):
    def authenticate(self, email: str | None = None) -> User:
        if not email or "@" not in email:
            raise ValueError("A valid email is required to sign in.")
        username = username_from_email(email)
        name = username.replace(".", " ").replace("_", " ").title()
        return User(username=username, email=email.strip().lower(), name=name)
