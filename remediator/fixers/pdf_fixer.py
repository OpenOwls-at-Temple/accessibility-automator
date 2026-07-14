"""PDF fixes D1-D21.

Phase 1 reliably auto-fixes the metadata checks (D2 title, D12 language). The
structural checks (D1 tagging, D3 alt text on untagged docs, D8 OCR, ...) cannot
be remediated correctly with pikepdf alone, so they are surfaced as ``not_fixed``
items carrying the auditor's recommendation — honest "needs human follow-up"
work rather than a placeholder that pretends the document is accessible.

OCR (D8) and structure-tree synthesis (D1/D3) are tracked as dedicated
follow-ups; see progress.md.
"""

from __future__ import annotations

from remediator.config import Config
from remediator.handlers.pdf_handler import (
    get_language,
    get_title,
    set_language,
    set_title,
)
from remediator.models import (
    ACTION_AUTO_FIXED,
    ACTION_NOT_FIXED,
    AuditResult,
    FixResult,
)

# Checks the fixer can correct deterministically; everything else is reported.
_AUTO_FIXABLE = {"D2", "D12"}


def fix_pdf(
    handler,
    audit_results: list[AuditResult],
    cfg: Config,
    provider=None,
    overrides: dict[str, str] | None = None,
) -> list[FixResult]:
    fixes: list[FixResult] = []

    # Unopenable (encrypted/corrupted): nothing can be fixed; report every issue.
    if handler.pdf is None:
        for r in audit_results:
            if not r.passed:
                fixes.append(
                    FixResult(
                        r.check_id,
                        ACTION_NOT_FIXED,
                        r.element_ref,
                        f"{r.detail}. {r.recommendation}".strip(),
                        success=False,
                    )
                )
        return fixes

    pdf = handler.pdf
    fixed: set[str] = set()

    # D2 — document title (Major, deterministic)
    if cfg.fixes.auto_fix_major and not get_title(pdf):
        title = handler.path.stem
        set_title(pdf, title)
        fixes.append(FixResult("D2", ACTION_AUTO_FIXED, "Document", f"Set document title: {title}"))
        fixed.add("D2")

    # D12 — document language (Minor, deterministic)
    if cfg.fixes.auto_fix_minor and not get_language(pdf):
        set_language(pdf, cfg.signoff.default_language)
        fixes.append(
            FixResult(
                "D12",
                ACTION_AUTO_FIXED,
                "Document",
                f"Set language to {cfg.signoff.default_language}",
            )
        )
        fixed.add("D12")

    # Everything else that failed needs structural work / OCR — report honestly.
    for r in audit_results:
        if r.passed or r.check_id in fixed:
            continue
        fixes.append(
            FixResult(
                r.check_id,
                ACTION_NOT_FIXED,
                r.element_ref,
                f"{r.detail}. {r.recommendation}".strip(),
                success=False,
            )
        )

    return fixes
