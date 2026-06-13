"""Signed session tokens (stdlib HMAC — no extra dependency).

A token is ``base64url(payload).base64url(hmac_sha256(payload))``. We only need
integrity (the server trusts the username inside), so this is a compact signed
cookie rather than full JWT. Tampering fails the constant-time signature check.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

COOKIE_NAME = "a11y_session"
_MAX_AGE_SECONDS = 60 * 60 * 12  # 12 hours


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(body: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return _b64e(digest)


def issue(payload: dict, secret: str) -> str:
    data = {**payload, "iat": int(time.time())}
    body = _b64e(json.dumps(data, separators=(",", ":")).encode())
    return f"{body}.{_sign(body, secret)}"


def verify(token: str, secret: str) -> dict | None:
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _sign(body, secret)):
        return None
    try:
        payload = json.loads(_b64d(body))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(time.time()) - int(payload.get("iat", 0)) > _MAX_AGE_SECONDS:
        return None
    return payload
