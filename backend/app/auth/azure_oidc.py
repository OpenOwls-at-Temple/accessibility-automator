"""Azure AD / Temple SSO provider — stub.

Wiring real OAuth2/OIDC (authorization-code redirect to the Temple login,
tenant restriction, token validation) is an early Phase 1 task gated on Temple
IT app registration (client id/secret, tenant id, redirect URI). Until then the
app runs with ``AUTH_PROVIDER=mock``. See ai_specs/architecture-planning.md
§Authentication.
"""

from __future__ import annotations

from backend.app.auth.base import AuthProvider
from backend.app.auth.models import User
from backend.app.settings import Settings


class AzureOIDCProvider(AuthProvider):
    def __init__(self, settings: Settings):
        self.settings = settings

    def authenticate(self, email: str | None = None) -> User:  # pragma: no cover - stub
        raise NotImplementedError(
            "Azure SSO is not wired yet — requires Temple IT app registration. "
            "Use AUTH_PROVIDER=mock for local development."
        )
