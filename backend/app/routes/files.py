"""File upload, download, and placeholder sign-off (all group-scoped)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend.app.auth.models import User
from backend.app.deps import get_current_user, get_jobs, get_storage
from backend.app.schemas.models import ApplyReviewRequest, JobOut, SignoffRequest, SuggestionItemOut, UploadResult
from backend.app.services.jobs import JobManager
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


@router.post("/{group}/files/{name}/scan", response_model=list[SuggestionItemOut])
def scan_file(
    group: str,
    name: str,
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> list[SuggestionItemOut]:
    """Audit a file and return AI draft suggestions for human review (no file written)."""
    from remediator.config import load_config
    from remediator.pipeline import scan_file as _scan

    input_path = storage.input_path(user.username, group, name)
    if not input_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    try:
        cfg = load_config()
        suggestions = _scan(input_path, cfg)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return [
        SuggestionItemOut(
            check_id=s.check_id,
            element_ref=s.element_ref,
            suggestion_type=s.suggestion_type,
            draft_text=s.draft_text,
            is_placeholder=s.is_placeholder,
        )
        for s in suggestions
    ]


@router.post("/{group}/files/{name}/apply-review", response_model=JobOut)
def apply_review(
    group: str,
    name: str,
    body: ApplyReviewRequest,
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
    jobs: JobManager = Depends(get_jobs),
) -> JobOut:
    """Apply human-approved suggestions and remediate the file."""
    input_path = storage.input_path(user.username, group, name)
    if not input_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    overrides = {s.element_ref: s.approved_text for s in body.suggestions}
    job = jobs.start(user.username, group, [name], overrides=overrides)
    return JobOut(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        files_done=job.files_done,
        files_total=job.files_total,
        current_file=job.current_file,
    )


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
