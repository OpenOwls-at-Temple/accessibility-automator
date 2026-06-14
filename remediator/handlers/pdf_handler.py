"""PDF handler + low-level pikepdf helpers shared by the rules and fixer.

pikepdf is a low-level library: it can reliably read/write document metadata
(title, language) and inspect the catalog, page resources, and structure tree,
but it cannot easily *synthesize* a full logical structure tree. So Phase 1
auto-fixes the metadata checks and reliably **detects** the structural ones,
reporting them for human follow-up (see architecture-planning.md risk note on
D1/D4/D7 and the OCR scope on D8).

If a file cannot be opened (encrypted without a password, or corrupted) the
handler records that state and ``save()`` copies the original through unchanged,
so the pipeline still produces an honest report instead of crashing.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pikepdf

from remediator.handlers.base import FormatHandler

_IMAGE = pikepdf.Name("/Image")


class PdfHandler(FormatHandler):
    file_type = "pdf"

    def __init__(self, path: str | Path):
        super().__init__(path)
        self.encrypted = False
        self.malformed = False
        self.pdf: pikepdf.Pdf | None = None
        try:
            self.pdf = pikepdf.open(str(self.path))
        except pikepdf.PasswordError:
            self.encrypted = True
        except Exception:  # noqa: BLE001 — any open failure => treat as malformed
            self.malformed = True

    def save(self, output_path: str | Path) -> None:
        if self.pdf is not None:
            self.pdf.save(str(output_path))
        else:
            # Unopenable (encrypted/corrupted): never lose the original.
            shutil.copyfile(self.path, output_path)

    @classmethod
    def supported_extensions(cls) -> tuple[str, ...]:
        return (".pdf",)


# ── pikepdf helpers (module-level so rules and fixers can reuse them) ──


def is_tagged(pdf: pikepdf.Pdf) -> bool:
    """True if the PDF declares a logical structure tree and is marked tagged."""
    root = pdf.Root
    if "/StructTreeRoot" not in root:
        return False
    mark = root.get("/MarkInfo")
    if mark is None:
        return False
    return bool(mark.get("/Marked", False))


def get_title(pdf: pikepdf.Pdf) -> str:
    title = pdf.docinfo.get("/Title")
    if title:
        return str(title).strip()
    try:
        with pdf.open_metadata() as meta:
            return str(meta.get("dc:title", "")).strip()
    except Exception:  # noqa: BLE001
        return ""


def set_title(pdf: pikepdf.Pdf, title: str) -> None:
    pdf.docinfo["/Title"] = title
    try:
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["dc:title"] = title
    except Exception:  # noqa: BLE001 — docinfo alone still satisfies most checkers
        pass


def get_language(pdf: pikepdf.Pdf) -> str:
    lang = pdf.Root.get("/Lang")
    return str(lang).strip() if lang else ""


def set_language(pdf: pikepdf.Pdf, lang: str) -> None:
    pdf.Root.Lang = pikepdf.String(lang)


def iter_image_xobjects(pdf: pikepdf.Pdf):
    """Yield (page_number, xobject_name) for every image on every page."""
    for page_num, page in enumerate(pdf.pages, start=1):
        resources = page.get("/Resources")
        if not resources:
            continue
        xobjects = resources.get("/XObject")
        if not xobjects:
            continue
        for name, xobj in xobjects.items():
            if xobj.get("/Subtype") == _IMAGE:
                yield page_num, str(name)


_TEXT_OPERATORS = {"Tj", "TJ", "'", '"'}


def _page_has_text(page) -> bool:
    """True if the page's content stream actually shows text (not just declares
    a font resource — some generators add fonts to image-only pages)."""
    try:
        for instruction in pikepdf.parse_content_stream(page):
            operator = getattr(instruction, "operator", None)
            if operator is None:  # older pikepdf yields (operands, operator) tuples
                operator = instruction[1]
            if str(operator) in _TEXT_OPERATORS:
                return True
        return False
    except Exception:  # noqa: BLE001 — fall back to the font-resource heuristic
        return bool((page.get("/Resources") or {}).get("/Font"))


def page_is_image_only(page) -> bool:
    """A page with image(s) but no rendered text is almost certainly a scan."""
    resources = page.get("/Resources")
    if not resources:
        return False
    xobjects = resources.get("/XObject")
    has_image = bool(xobjects and any(x.get("/Subtype") == _IMAGE for x in xobjects.values()))
    return has_image and not _page_has_text(page)


def iter_link_annotations(pdf: pikepdf.Pdf):
    """Yield (page_number, annotation) for every link annotation with a URI."""
    for page_num, page in enumerate(pdf.pages, start=1):
        for annot in page.get("/Annots", []) or []:
            if annot.get("/Subtype") != pikepdf.Name("/Link"):
                continue
            action = annot.get("/A")
            if action is not None and action.get("/URI") is not None:
                yield page_num, annot
