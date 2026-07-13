"""Remediation reports — per-file JSON and rendered HTML."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from backend.app.deps import get_current_user, get_storage
from backend.app.models.user import User
from backend.app.services.storage import StorageError, StorageService

router = APIRouter(prefix="/groups", tags=["reports"])


@router.get("/{group}/files/{name}/report")
def file_report_json(
    group: str,
    name: str,
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> dict:
    try:
        path = storage.report_path(user.username, group, name, kind="json")
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/{group}/files/{name}/report/html", response_class=HTMLResponse)
def file_report_html(
    group: str,
    name: str,
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> HTMLResponse:
    try:
        path = storage.report_path(user.username, group, name, kind="html")
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return HTMLResponse(path.read_text(encoding="utf-8"))
