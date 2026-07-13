"""Shared column helpers for ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import mapped_column


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def uuid_pk():
    return mapped_column(String(36), primary_key=True, default=new_uuid)


def created_at_column():
    return mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
