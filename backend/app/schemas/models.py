"""API request/response shapes."""

from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str


class FileOut(BaseModel):
    name: str
    file_type: str
    has_output: bool
    pre_fix_score: int | None = None
    post_fix_score: int | None = None
    truly_remediated_score: int | None = None
    status: str


class GroupSummary(BaseModel):
    name: str
    file_count: int


class GroupDetail(BaseModel):
    name: str
    files: list[FileOut]


class RemediateRequest(BaseModel):
    files: list[str] | None = None  # default: all input files in the group


class JobOut(BaseModel):
    job_id: str
    status: str
    progress: float
    files_done: int
    files_total: int
    current_file: str | None = None
    error: str | None = None


class SuggestionItemOut(BaseModel):
    check_id: str
    element_ref: str
    suggestion_type: str   # "alt_text" | "slide_title"
    draft_text: str
    is_placeholder: bool


class ApprovedSuggestion(BaseModel):
    check_id: str
    element_ref: str
    approved_text: str


class ApplyReviewRequest(BaseModel):
    suggestions: list[ApprovedSuggestion]


class SignoffRequest(BaseModel):
    check_id: str
    action: str = "acknowledge"
    note: str | None = None


class UploadResult(BaseModel):
    saved: list[str]
    group: str
