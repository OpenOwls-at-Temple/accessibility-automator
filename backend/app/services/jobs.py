"""Background remediation jobs with status polling.

LLM captioning is slow on big decks, so remediation runs off the request thread
and the frontend polls ``GET /jobs/{id}``. Jobs are processed one file at a time
(predictable cost; matches the spec). Job state is in-memory — fine for Phase 1's
single-process deployment; a future multi-worker setup would move this to a store.
"""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from backend.app.services.storage import StorageService
from remediator.config import Config
from remediator.llm.provider import build_provider
from remediator.pipeline import remediate_file
from remediator.reporter import write_html_report, write_json_report

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_ERROR = "error"


@dataclass
class Job:
    id: str
    username: str
    group: str
    files: list[str]
    status: str = STATUS_QUEUED
    files_done: int = 0
    error: str | None = None

    @property
    def files_total(self) -> int:
        return len(self.files)

    @property
    def progress(self) -> float:
        return self.files_done / self.files_total if self.files_total else 1.0


class JobManager:
    def __init__(self, storage: StorageService, config: Config, max_workers: int = 2):
        self.storage = storage
        self.config = config
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def start(self, username: str, group: str, files: list[str]) -> Job:
        job = Job(id=uuid.uuid4().hex, username=username, group=group, files=files)
        with self._lock:
            self._jobs[job.id] = job
        self._executor.submit(self._run, job)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _run(self, job: Job) -> None:
        job.status = STATUS_RUNNING
        # One provider per job; None when no LLM is configured (-> placeholders).
        provider = build_provider(self.config.llm)
        try:
            for filename in job.files:
                self._remediate_one(job, filename, provider)
                job.files_done += 1
            job.status = STATUS_DONE
        except Exception as exc:  # noqa: BLE001 — record, never crash the worker
            job.status = STATUS_ERROR
            job.error = str(exc)

    def _remediate_one(self, job: Job, filename: str, provider) -> None:
        input_path = self.storage.input_path(job.username, job.group, filename)
        output_path = self.storage.output_path(job.username, job.group, filename)
        try:
            report = remediate_file(input_path, output_path, cfg=self.config, provider=provider)
            write_json_report(report, self.storage.report_path(job.username, job.group, filename))
            write_html_report(
                report, self.storage.report_path(job.username, job.group, filename, kind="html")
            )
            self.storage.update_file_scores(job.username, job.group, filename, report)
        except Exception:
            self.storage.set_file_status(job.username, job.group, filename, "error")
            raise
