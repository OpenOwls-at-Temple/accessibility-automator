"""Group listing and remediation kickoff. Groups organize a user's files
(usually by course code)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.auth.models import User
from backend.app.deps import get_current_user, get_jobs, get_storage
from backend.app.schemas.models import (
    FileOut,
    GroupDetail,
    GroupSummary,
    JobOut,
    RemediateRequest,
)
from backend.app.services.jobs import JobManager
from backend.app.services.storage import StorageError, StorageService

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupSummary])
def list_groups(
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> list[GroupSummary]:
    return [
        GroupSummary(name=g, file_count=len(storage.list_group_files(user.username, g)))
        for g in storage.list_groups(user.username)
    ]


@router.get("/{group}", response_model=GroupDetail)
def get_group(
    group: str,
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
) -> GroupDetail:
    try:
        files = storage.list_group_files(user.username, group)
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return GroupDetail(name=group, files=[FileOut(**vars(f)) for f in files])


@router.post("/{group}/remediate", response_model=JobOut)
def remediate_group(
    group: str,
    body: RemediateRequest,
    user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
    jobs: JobManager = Depends(get_jobs),
) -> JobOut:
    try:
        existing = {f.name for f in storage.list_group_files(user.username, group)}
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group has no files")

    files = body.files or sorted(existing)
    unknown = [f for f in files if f not in existing]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown files: {unknown}"
        )

    job = jobs.start(user.username, group, files)
    return JobOut(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        files_done=job.files_done,
        files_total=job.files_total,
        current_file=job.current_file,
    )
