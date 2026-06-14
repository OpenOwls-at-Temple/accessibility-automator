"""Expose the effective (non-secret) engine configuration, read-only."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from backend.app.auth.models import User
from backend.app.deps import get_config, get_current_user
from remediator.config import Config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def get_effective_config(
    config: Config = Depends(get_config),
    _: User = Depends(get_current_user),
) -> dict:
    return asdict(config)
