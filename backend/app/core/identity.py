"""Derive a filesystem-safe workspace key from a user's email.

The workspace on disk (input/output folders) is keyed by this value, so it must
be stable and free of path separators. The authenticated user's email is the
source of truth — never a client-supplied path.
"""

from __future__ import annotations

import re

_UNSAFE = re.compile(r"[^a-z0-9._-]+")


def username_from_email(email: str) -> str:
    """`Alex.Pang@temple.edu` -> `alex.pang` (safe workspace folder name)."""
    local = email.strip().lower().split("@", 1)[0]
    cleaned = _UNSAFE.sub("", local)
    return cleaned or "user"
