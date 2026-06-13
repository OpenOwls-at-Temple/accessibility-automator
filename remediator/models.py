"""Shared engine data models.

These dataclasses are format-agnostic: PPTX rules (P#) and PDF rules (D#) both
produce :class:`AuditResult` / :class:`FixResult`, and the shared scorer and
reporter consume them. Keeping them here lets every format speak one language.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── Severity levels (used as dict keys into the scorer's weights) ──
SEVERITY_SEVERE = "Severe"
SEVERITY_MAJOR = "Major"
SEVERITY_MINOR = "Minor"
SEVERITY_DISABLED = "Disabled"

# ── Fix actions (FixResult.action) ──
ACTION_AUTO_FIXED = "auto_fixed"
ACTION_AI_FIXED = "ai_fixed"
ACTION_PLACEHOLDER = "placeholder"
ACTION_NOT_FIXED = "not_fixed"


@dataclass
class AuditResult:
    """The outcome of evaluating one accessibility check against one element.

    A check (e.g. ``P3`` image alt text) may produce many results — one per
    image. The scorer groups by ``check_id``: a check passes only if every one
    of its results passed.
    """

    check_id: str  # "P3"
    severity: str  # SEVERITY_*
    passed: bool
    element_ref: str  # "Slide 4 / Picture 7"
    detail: str = ""
    recommendation: str = ""


@dataclass
class FixResult:
    """The outcome of attempting to fix one violation."""

    check_id: str
    action: str  # ACTION_*
    element_ref: str
    detail: str = ""
    success: bool = True


@dataclass
class ScoreBreakdown:
    """A single computed score plus the numbers behind it (for transparency)."""

    score: int  # 0-100
    total_weight: int
    weighted_passes: int
    capped: bool = False  # True if a remaining Severe violation capped the score

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "total_weight": self.total_weight,
            "weighted_passes": self.weighted_passes,
            "capped": self.capped,
        }


@dataclass
class FileReport:
    """The full before/after record for one remediated file.

    Surfaces **two** post-fix scores on purpose (see domain-knowledge.md):

    * ``post_fix_score`` — checker-passing: placeholders count as passing.
    * ``truly_remediated_score`` — placeholders count as failing.

    The gap between them is exactly the human follow-up backlog.
    """

    file_name: str
    file_type: str  # "pptx" | "pdf"
    pre_fix_audit: list[AuditResult] = field(default_factory=list)
    fixes: list[FixResult] = field(default_factory=list)
    post_fix_audit: list[AuditResult] = field(default_factory=list)
    pre_fix: ScoreBreakdown | None = None
    post_fix: ScoreBreakdown | None = None
    truly_remediated: ScoreBreakdown | None = None

    @property
    def pre_fix_score(self) -> int:
        return self.pre_fix.score if self.pre_fix else 0

    @property
    def post_fix_score(self) -> int:
        return self.post_fix.score if self.post_fix else 0

    @property
    def truly_remediated_score(self) -> int:
        return self.truly_remediated.score if self.truly_remediated else 0

    @property
    def placeholder_fixes(self) -> list[FixResult]:
        """Items that pass the checker but still need a human (the backlog)."""
        return [f for f in self.fixes if f.action == ACTION_PLACEHOLDER]
