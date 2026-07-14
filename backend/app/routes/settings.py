"""Per-user settings. Currently just the remediated-filename suffix."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.deps import get_current_user, get_storage
from backend.app.models.user import User
from backend.app.schemas.models import SettingsOut, SettingsUpdate
from backend.app.services.storage import StorageError, StorageService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> SettingsOut:
    return SettingsOut(**storage.get_user_settings(user.username))


@router.put("", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate,
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> SettingsOut:
    try:
        storage.set_filename_suffix(user.username, body.filename_suffix)
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SettingsOut(**storage.get_user_settings(user.username))
