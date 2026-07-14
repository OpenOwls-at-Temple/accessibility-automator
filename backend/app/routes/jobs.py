"""Job status polling. A user can only see their own jobs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.deps import get_current_user, get_jobs
from backend.app.models.user import User
from backend.app.schemas.models import JobOut
from backend.app.services.jobs import JobManager

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    jobs: JobManager = Depends(get_jobs),
) -> JobOut:
    job = jobs.get(job_id)
    # Same 404 whether the job is missing or belongs to someone else — never
    # reveal another user's job ids.
    if job is None or job.username != user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobOut(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        files_done=job.files_done,
        files_total=job.files_total,
        current_file=job.current_file,
        error=job.error,
    )
