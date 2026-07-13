"""File upload, download, and placeholder sign-off (all group-scoped)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend.app.deps import get_current_user, get_storage
from backend.app.models.user import User
from backend.app.schemas.models import SignoffRequest, UploadResult
from backend.app.services.storage import StorageError, StorageService

router = APIRouter(prefix="/groups", tags=["files"])


@router.post("/{group}/files", response_model=UploadResult)
async def upload_files(
    group: str,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> UploadResult:
    saved = []
    for upload in files:
        data = await upload.read()
        try:
            storage.save_upload(user.username, group, upload.filename, data)
        except StorageError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        saved.append(upload.filename)
    return UploadResult(saved=saved, group=group)


@router.get("/{group}/files/{name}/download")
def download_file(
    group: str,
    name: str,
    kind: str = "output",
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> FileResponse:
    if kind not in ("input", "output"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="kind must be input|output"
        )
    try:
        if kind == "input":
            path = storage.input_path(user.username, group, name)
            download_name = name
        else:
            path = storage.output_path(user.username, group, name)
            download_name = path.name
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(str(path), filename=download_name)


@router.post("/{group}/files/{name}/signoff")
def signoff(
    group: str,
    name: str,
    body: SignoffRequest,
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> dict:
    try:
        ok = storage.acknowledge_signoff(user.username, group, name, body.check_id, body.note)
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sign-off item not found")
    return {"ok": True}
