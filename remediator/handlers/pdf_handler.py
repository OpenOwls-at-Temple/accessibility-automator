"""PDF handler — stub.

Phase 1 PDF path (pikepdf + OCR) is implemented after the PPTX path is complete.
See ai_specs/architecture-planning.md (D1-D21) and the risk note on PDF
structural tagging.
"""

from __future__ import annotations

from pathlib import Path

from remediator.handlers.base import FormatHandler


class PdfHandler(FormatHandler):
    file_type = "pdf"

    def __init__(self, path: str | Path):
        super().__init__(path)
        raise NotImplementedError("PDF handling is not implemented yet (Phase 1, next).")

    def save(self, output_path: str | Path) -> None:  # pragma: no cover - stub
        raise NotImplementedError

    @classmethod
    def supported_extensions(cls) -> tuple[str, ...]:
        return (".pdf",)
