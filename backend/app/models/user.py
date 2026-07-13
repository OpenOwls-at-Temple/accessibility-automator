"""The user allowlist.

A row here is an *invitation*: only emails an admin has added can sign in
(Google verifies identity; this table decides authorization). Sign-in never
auto-provisions. The ``username`` is derived from the email and keys the user's
filesystem workspace — the database stores who; the disk stores their files.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.core.identity import username_from_email
from backend.app.models.base import created_at_column, uuid_pk


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def username(self) -> str:
        """Filesystem workspace key derived from the email local-part."""
        return username_from_email(self.email)
