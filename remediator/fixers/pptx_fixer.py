"""Deterministic PPTX fixes + orchestration of the AI fixes.

Scans the live presentation and repairs each violation, mirroring the checks in
``rules/pptx_rules.py``. Report-only checks (P4 contrast, P8 link text, P9 font
size) are passed through as ``not_fixed`` items carrying the auditor's
recommendation, so they surface in the report for manual follow-up.
"""

from __future__ import annotations

from remediator.config import Config
from remediator.fixers import ai_fixer
from remediator.handlers.pptx_handler import (
    PptxHandler,
    get_alt_text,
    is_decorative,
    is_meaningful_alt_text,
)
from remediator.models import (
    ACTION_AUTO_FIXED,
    ACTION_NOT_FIXED,
    AuditResult,
    FixResult,
)
from remediator.rules import pptx_rules as rules

_REPORT_ONLY_CHECKS = {"P4", "P8", "P9"}


def _slide_text(slide) -> str:
    parts = []
    for shape in rules._walk_shapes(slide.shapes):
        if shape.has_text_frame and shape.text.strip():
            parts.append(shape.text.strip())
    return "\n".join(parts)


def _derive_doc_title(prs, handler: PptxHandler) -> str:
    for slide in prs.slides:
        title = slide.shapes.title
        if title is not None and (title.text or "").strip():
            return title.text.strip()
    return handler.path.stem


def _set_run_lang(run, lang: str) -> None:
    run._r.get_or_add_rPr().set("lang", lang)


def _needs_reorder(slide) -> bool:
    positioned = [s for s in slide.shapes if s.top is not None and s.left is not None]
    if len(positioned) < 2:
        return False
    current = [id(s._element) for s in positioned]
    ordered = [id(s._element) for s in sorted(positioned, key=lambda s: (s.top, s.left))]
    return current != ordered


def _reorder_slide(slide) -> None:
    positioned = [s for s in slide.shapes if s.top is not None and s.left is not None]
    sp_tree = slide.shapes._spTree
    for shape in sorted(positioned, key=lambda s: (s.top, s.left)):
        sp_tree.remove(shape._element)
        sp_tree.append(shape._element)


def fix_pptx(
    handler: PptxHandler,
    audit_results: list[AuditResult],
    cfg: Config,
    provider=None,
) -> list[FixResult]:
    prs = handler.presentation
    fixes: list[FixResult] = []
    fix_major = cfg.fixes.auto_fix_major
    fix_minor = cfg.fixes.auto_fix_minor

    # P1 — document title (Major, deterministic)
    if fix_major and not (prs.core_properties.title or "").strip():
        title = _derive_doc_title(prs, handler)
        prs.core_properties.title = title
        fixes.append(FixResult("P1", ACTION_AUTO_FIXED, "Document", f"Set document title: {title}"))

    # P2 — slide titles (Major, AI + placeholder)
    for s_idx, slide in enumerate(prs.slides, start=1):
        title_shape = slide.shapes.title
        if title_shape is not None and (title_shape.text or "").strip():
            continue
        fixes.append(
            ai_fixer.fix_slide_title(
                slide, s_idx, rules._slide_label(s_idx), _slide_text(slide), cfg, provider
            )
        )

    # P3 — image alt text (Major, AI + placeholder)
    for s_idx, shape in rules.iter_pictures(prs):
        if is_decorative(shape) or is_meaningful_alt_text(get_alt_text(shape)):
            continue
        slide = prs.slides[s_idx - 1]
        title = slide.shapes.title
        context = (title.text or "").strip() if title is not None else ""
        fixes.append(
            ai_fixer.fix_image_alt_text(shape, rules._ref(s_idx, shape), context, cfg, provider)
        )

    # P5 — table headers (Major, deterministic)
    if fix_major:
        for s_idx, slide in enumerate(prs.slides, start=1):
            for shape in rules._walk_shapes(slide.shapes):
                if shape.has_table and not shape.table.first_row:
                    shape.table.first_row = True
                    fixes.append(
                        FixResult(
                            "P5",
                            ACTION_AUTO_FIXED,
                            rules._ref(s_idx, shape),
                            "Marked first row as header",
                        )
                    )

    # P6 — document language (Minor, deterministic)
    if fix_minor:
        runs = list(rules.iter_runs(prs))
        if runs and not any(rules._run_lang(run) for _, _, run in runs):
            for _, _, run in runs:
                _set_run_lang(run, cfg.signoff.default_language)
            fixes.append(
                FixResult(
                    "P6",
                    ACTION_AUTO_FIXED,
                    "Document",
                    f"Set language to {cfg.signoff.default_language}",
                )
            )

        # P7 — repair empty language tags (Minor, deterministic)
        for s_idx, shape, run in rules.iter_runs(prs):
            lang = rules._run_lang(run)
            if lang is not None and not lang.strip():
                _set_run_lang(run, cfg.signoff.default_language)
                fixes.append(
                    FixResult(
                        "P7",
                        ACTION_AUTO_FIXED,
                        rules._ref(s_idx, shape),
                        f"Set language to {cfg.signoff.default_language}",
                    )
                )

        # P10 — reading order (Minor, deterministic, best-effort)
        for s_idx, slide in enumerate(prs.slides, start=1):
            if _needs_reorder(slide):
                try:
                    _reorder_slide(slide)
                    fixes.append(
                        FixResult(
                            "P10",
                            ACTION_AUTO_FIXED,
                            rules._slide_label(s_idx),
                            "Reset reading order top-to-bottom, left-to-right",
                        )
                    )
                except Exception as exc:  # noqa: BLE001 — never crash the job
                    fixes.append(
                        FixResult(
                            "P10",
                            ACTION_NOT_FIXED,
                            rules._slide_label(s_idx),
                            f"Could not reorder: {exc}",
                            success=False,
                        )
                    )

    # Report-only checks (P4, P8, P9): surface as needs-manual-fix items.
    for r in audit_results:
        if r.check_id in _REPORT_ONLY_CHECKS and not r.passed:
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
