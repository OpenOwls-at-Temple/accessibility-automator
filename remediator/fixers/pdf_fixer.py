"""PDF fixes (incl. OCR) D1-D21 — stub (implemented after the PPTX path)."""

from __future__ import annotations

from remediator.config import Config
from remediator.models import AuditResult, FixResult


def fix_pdf(  # pragma: no cover - stub
    handler, audit_results: list[AuditResult], cfg: Config, provider=None
) -> list[FixResult]:
    raise NotImplementedError("PDF fixes (D1-D21) are not implemented yet.")
