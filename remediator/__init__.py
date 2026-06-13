"""Accessibility Automator remediation engine.

A standalone package that audits, fixes, re-scores, and reports on the
accessibility of documents (PPTX in Phase 1, PDF next). It is decoupled from
the web layer: it may be imported by ``backend/`` and run directly as a CLI,
but it **must never import from** ``backend/``. The dependency is one-way.

See ai_specs/architecture-planning.md.
"""

from remediator.models import AuditResult, FileReport, FixResult, ScoreBreakdown
from remediator.pipeline import remediate_file

__all__ = [
    "AuditResult",
    "FixResult",
    "FileReport",
    "ScoreBreakdown",
    "remediate_file",
]
