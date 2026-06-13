"""PDF audit checks D1-D21 (approximating the YuJa Panorama checklist).

Phase 1 reliably **detects** the checks that pikepdf can determine without a full
structure tree or page rendering, and auto-fixes only the metadata ones (the
fixer handles D2/D12). The remaining structural checks are reported for human
follow-up — this is the deliberate, honest scope from architecture-planning.md's
risk note (D1/D4/D7 structural tagging is the hardest area; OCR for D8 and
contrast/table detection that require rendering or a tag tree are deferred).

Checks implemented here: D1 (untagged), D2 (title), D3 (image alt text),
D8 (scanned), D9/D10/D11 (integrity), D12 (language), D16 (link text).
Tag-tree / render-dependent checks (D4-D7, D13-D15, D17-D21) are deferred and
documented rather than guessed at.
"""

from __future__ import annotations

from remediator.handlers.pdf_handler import (
    get_language,
    get_title,
    is_tagged,
    iter_image_xobjects,
    iter_link_annotations,
    page_is_image_only,
)
from remediator.models import (
    SEVERITY_MAJOR,
    SEVERITY_MINOR,
    SEVERITY_SEVERE,
    AuditResult,
)


def audit_pdf(handler) -> list[AuditResult]:
    results: list[AuditResult] = []

    # ── D9/D10/D11 integrity (Severe). If unopenable, nothing else is knowable.
    if handler.encrypted:
        results.append(
            AuditResult(
                "D10",
                SEVERITY_SEVERE,
                passed=False,
                element_ref="Document",
                detail="PDF is encrypted",
                recommendation="Remove the password/encryption before remediation.",
            )
        )
        return results
    if handler.malformed or handler.pdf is None:
        results.append(
            AuditResult(
                "D11",
                SEVERITY_SEVERE,
                passed=False,
                element_ref="Document",
                detail="PDF is malformed or corrupted",
                recommendation="Re-export the PDF from the source application.",
            )
        )
        return results

    pdf = handler.pdf
    results.append(AuditResult("D9", SEVERITY_SEVERE, True, "Document", "Well-formed PDF"))
    results.append(AuditResult("D10", SEVERITY_SEVERE, True, "Document", "Not encrypted"))

    # ── D1 tagged structure (Major)
    tagged = is_tagged(pdf)
    results.append(
        AuditResult(
            "D1",
            SEVERITY_MAJOR,
            passed=tagged,
            element_ref="Document",
            detail="Tagged PDF" if tagged else "PDF is untagged (no logical structure)",
            recommendation="" if tagged else "Add a tag structure (logical structure tree).",
        )
    )

    # ── D2 document title (Major)
    title = get_title(pdf)
    results.append(
        AuditResult(
            "D2",
            SEVERITY_MAJOR,
            passed=bool(title),
            element_ref="Document",
            detail=f"Title: {title!r}" if title else "Document has no title",
            recommendation="" if title else "Set the document title.",
        )
    )

    # ── D12 language (Minor)
    lang = get_language(pdf)
    results.append(
        AuditResult(
            "D12",
            SEVERITY_MINOR,
            passed=bool(lang),
            element_ref="Document",
            detail=f"Language: {lang}" if lang else "No language specified",
            recommendation="" if lang else "Set the document language (/Lang).",
        )
    )

    # ── D8 scanned / image-only pages (Severe)
    for page_num, page in enumerate(pdf.pages, start=1):
        if page_is_image_only(page):
            results.append(
                AuditResult(
                    "D8",
                    SEVERITY_SEVERE,
                    passed=False,
                    element_ref=f"Page {page_num}",
                    detail="Scanned (image-only) page — no text layer",
                    recommendation="Run OCR to add a searchable text layer.",
                )
            )

    # ── D3 image alt text (Major)
    images = list(iter_image_xobjects(pdf))
    if images:
        if not tagged:
            results.append(
                AuditResult(
                    "D3",
                    SEVERITY_MAJOR,
                    passed=False,
                    element_ref=f"{len(images)} image(s)",
                    detail="Images have no alt text (document is untagged)",
                    recommendation="Tag images as figures, then add alt text.",
                )
            )
        else:
            # Tagged: alt text would live on Figure structure elements. Detecting
            # per-figure /Alt reliably needs full structure-tree walking; flag for
            # review in Phase 1 rather than report a false pass.
            results.append(
                AuditResult(
                    "D3",
                    SEVERITY_MAJOR,
                    passed=False,
                    element_ref=f"{len(images)} image(s)",
                    detail="Tagged PDF — verify each figure has alt text",
                    recommendation="Confirm /Alt is set on every Figure element.",
                )
            )

    # ── D16 link text (Minor, report-only)
    links = list(iter_link_annotations(pdf))
    if links:
        results.append(
            AuditResult(
                "D16",
                SEVERITY_MINOR,
                passed=False,
                element_ref=f"{len(links)} link(s)",
                detail="Link annotations present — verify descriptive link text",
                recommendation="Ensure link text describes the destination.",
            )
        )

    return results
