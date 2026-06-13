"""The remediation pipeline: audit -> fix -> re-score -> report.

Format-agnostic orchestration. A per-format entry in ``_REGISTRY`` binds a
handler, an audit function, and a fix function; adding PDF (or Word in Phase 2)
means adding one registry entry, not changing this file.
"""

from __future__ import annotations

from pathlib import Path

from remediator.config import Config, load_config
from remediator.fixers import pptx_fixer
from remediator.handlers.pptx_handler import PptxHandler
from remediator.llm.provider import build_provider
from remediator.models import ACTION_PLACEHOLDER, FileReport
from remediator.rules import pptx_rules
from remediator.scorer import compute_score

# extension -> (handler class, audit fn, fix fn)
_REGISTRY = {
    ".pptx": (PptxHandler, pptx_rules.audit_pptx, pptx_fixer.fix_pptx),
}


def supported_extensions() -> tuple[str, ...]:
    return tuple(_REGISTRY)


def remediate_file(
    input_path: str | Path,
    output_path: str | Path,
    cfg: Config | None = None,
    provider="__build__",
) -> FileReport:
    """Remediate one file and return its before/after report.

    ``provider`` defaults to building one from config + environment; pass an
    explicit provider (or ``None`` to force placeholder-only) for tests.
    """
    input_path, output_path = Path(input_path), Path(output_path)
    cfg = cfg or load_config()
    ext = input_path.suffix.lower()
    if ext not in _REGISTRY:
        raise NotImplementedError(
            f"Unsupported file type {ext!r}; supported: {supported_extensions()}"
        )
    handler_cls, audit_fn, fix_fn = _REGISTRY[ext]

    if provider == "__build__":
        provider = build_provider(cfg.llm)

    # 1. Audit the input -> pre-fix score.
    handler = handler_cls(input_path)
    pre_audit = audit_fn(handler)
    pre_score = compute_score(pre_audit, cfg.scoring)

    # 2. Fix, then write the remediated copy (originals are never touched).
    fixes = fix_fn(handler, pre_audit, cfg, provider)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    handler.save(output_path)

    # 3. Re-audit the output -> checker-passing + truly-remediated scores.
    post_handler = handler_cls(output_path)
    post_audit = audit_fn(post_handler)
    post_score = compute_score(post_audit, cfg.scoring)
    placeholder_checks = {f.check_id for f in fixes if f.action == ACTION_PLACEHOLDER}
    truly_score = compute_score(post_audit, cfg.scoring, placeholder_checks)

    return FileReport(
        file_name=input_path.name,
        file_type=handler.file_type,
        pre_fix_audit=pre_audit,
        fixes=fixes,
        post_fix_audit=post_audit,
        pre_fix=pre_score,
        post_fix=post_score,
        truly_remediated=truly_score,
    )
