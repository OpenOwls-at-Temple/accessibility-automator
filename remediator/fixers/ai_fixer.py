"""AI-backed fixes: image alt text (P3/D3) and slide titles (P2).

Every path degrades safely: if the LLM is disabled, errors, or returns
low-confidence output, the item becomes a **placeholder** that passes the
checker but is flagged for human follow-up — a remediation job never crashes on
an LLM failure (ai_specs/conventions.md, ai_specs/llm-integration.md).
"""

from __future__ import annotations

from remediator.config import Config
from remediator.handlers.pptx_handler import mark_decorative, set_alt_text
from remediator.llm.provider import LLMError
from remediator.models import (
    ACTION_AI_FIXED,
    ACTION_NOT_FIXED,
    ACTION_PLACEHOLDER,
    FixResult,
)


def _placeholder_or_unfixed(
    check_id: str, element_ref: str, cfg: Config, write, detail_unfixed: str
) -> FixResult:
    """Apply the configured placeholder, or leave the item failing."""
    if cfg.signoff.add_placeholder_for_unfixable:
        write()
        return FixResult(
            check_id,
            ACTION_PLACEHOLDER,
            element_ref,
            detail="Placeholder written — needs human follow-up",
            success=True,
        )
    return FixResult(check_id, ACTION_NOT_FIXED, element_ref, detail_unfixed, success=False)


def fix_image_alt_text(shape, element_ref: str, context: str, cfg: Config, provider) -> FixResult:
    """Caption an image with the LLM, falling back to a placeholder."""

    def placeholder():
        set_alt_text(shape, cfg.signoff.placeholder_alt_text)

    if provider is None or not cfg.llm.generate_alt_text:
        return _placeholder_or_unfixed(
            "P3", element_ref, cfg, placeholder, "LLM disabled; no alt text"
        )

    try:
        image = shape.image
        result = provider.caption_image(image.blob, image.content_type, context)
    except (LLMError, Exception) as exc:  # noqa: BLE001 — degrade, never crash
        if isinstance(exc, LLMError):
            return _placeholder_or_unfixed("P3", element_ref, cfg, placeholder, f"LLM error: {exc}")
        # Non-LLM error (e.g. unreadable image): still degrade to placeholder.
        return _placeholder_or_unfixed(
            "P3", element_ref, cfg, placeholder, f"Could not read image: {exc}"
        )

    if result.decorative:
        mark_decorative(shape)
        return FixResult("P3", ACTION_AI_FIXED, element_ref, "Marked decorative", success=True)

    if result.alt_text and result.confidence >= cfg.llm.confidence_threshold:
        set_alt_text(shape, result.alt_text)
        return FixResult(
            "P3",
            ACTION_AI_FIXED,
            element_ref,
            f"Alt text (conf {result.confidence:.2f}): {result.alt_text}",
            success=True,
        )

    return _placeholder_or_unfixed(
        "P3",
        element_ref,
        cfg,
        placeholder,
        f"Low confidence ({result.confidence:.2f}); no alt text",
    )


def fix_slide_title(
    slide, slide_idx: int, element_ref: str, slide_text: str, cfg: Config, provider
) -> FixResult:
    """Suggest a slide title with the LLM, falling back to a placeholder.

    Requires a title placeholder to hold the text; if the slide layout provides
    none and one cannot be cloned, the item is left unfixed.
    """
    title_shape = _ensure_title_placeholder(slide)
    if title_shape is None:
        return FixResult(
            "P2", ACTION_NOT_FIXED, element_ref, "No title placeholder available", success=False
        )

    placeholder_title = f"{cfg.signoff.placeholder_slide_title_prefix} {slide_idx}"

    def write_placeholder():
        title_shape.text = placeholder_title

    if provider is None or not cfg.llm.suggest_titles or not slide_text.strip():
        return _placeholder_or_unfixed(
            "P2", element_ref, cfg, write_placeholder, "LLM disabled; no title"
        )

    try:
        result = provider.suggest_title(slide_text)
    except LLMError as exc:
        return _placeholder_or_unfixed(
            "P2", element_ref, cfg, write_placeholder, f"LLM error: {exc}"
        )

    if result.title and result.confidence >= cfg.llm.confidence_threshold:
        title_shape.text = result.title
        return FixResult(
            "P2",
            ACTION_AI_FIXED,
            element_ref,
            f"Title (conf {result.confidence:.2f}): {result.title}",
            success=True,
        )

    return _placeholder_or_unfixed(
        "P2",
        element_ref,
        cfg,
        write_placeholder,
        f"Low confidence ({result.confidence:.2f}); no title",
    )


def _ensure_title_placeholder(slide):
    """Return the slide's title placeholder, cloning the layout's if missing.

    ``SlideLayout.shapes``/``.placeholders`` have no ``.title`` shortcut (that
    convenience property only exists on ``SlideShapes``) - the title
    placeholder must be found by its idx, which is always 0 for both TITLE
    and CENTER_TITLE layouts.
    """
    if slide.shapes.title is not None:
        return slide.shapes.title
    import copy

    layout_title = None
    for ph in slide.slide_layout.placeholders:
        if ph.placeholder_format.idx == 0:
            layout_title = ph
            break
    if layout_title is None:
        return None
    try:
        cloned = copy.deepcopy(layout_title._element)
        slide.shapes._spTree.append(cloned)
        return slide.shapes.title
    except Exception:
        return None
