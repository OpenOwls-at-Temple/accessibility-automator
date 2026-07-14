"""PPTX handler + low-level OOXML helpers shared by the rules and fixer.

``python-pptx`` does not expose alt text or the "mark decorative" flag through
its public API, so the small XML helpers live here in one place rather than
being duplicated across the audit and fix code.
"""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree
from pptx import Presentation

from remediator.handlers.base import FormatHandler

# A single token ending in an image extension is a filename, not real alt text.
_FILENAME_ALT_RE = re.compile(r"^\S+\.(png|jpe?g|gif|bmp|tiff?|webp|emf|wmf|svg)$", re.IGNORECASE)

# Microsoft's "decorative image" extension (Office 2017+).
_DECORATIVE_EXT_URI = "{C183D7F6-B498-43B3-948B-1728B52AA6E4}"
_NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_NS_ADEC = "http://schemas.microsoft.com/office/drawing/2017/decorative"


class PptxHandler(FormatHandler):
    file_type = "pptx"

    def __init__(self, path: str | Path):
        super().__init__(path)
        self.presentation = Presentation(str(self.path))

    def save(self, output_path: str | Path) -> None:
        self.presentation.save(str(output_path))

    @classmethod
    def supported_extensions(cls) -> tuple[str, ...]:
        return (".pptx",)


# Characters lxml rejects when writing an XML attribute value or text node.
# PowerPoint stores soft line breaks in title/heading text as U+000B (vertical
# tab), which is legal inside a run but not as a bare XML string — writing it to
# ``core_properties.title`` or a ``descr`` attribute raises ``ValueError``.
_XML_ILLEGAL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def xml_safe_text(text: str) -> str:
    """Make text safe to write into OOXML: line/page breaks (U+000B/000C) become
    spaces and other control chars are dropped. Tabs/newlines are left as-is
    (they are valid XML). Returns ``text`` unchanged when it is already clean."""
    if not text:
        return text
    return _XML_ILLEGAL_RE.sub(lambda m: " " if m.group() in "\x0b\x0c" else "", text)


# ── OOXML helpers (module-level so rules and fixers can reuse them) ──


def find_cnvpr(shape) -> etree._Element | None:
    """Return a shape's own non-visual ``cNvPr`` element.

    Works across shape types (sp / pic / graphicFrame / grpSp) by matching on
    local name, so we do not depend on the namespace prefix. The shape's own
    ``cNvPr`` is the first one encountered in document order.
    """
    for el in shape._element.iter():
        if etree.QName(el).localname == "cNvPr":
            return el
    return None


def get_alt_text(shape) -> str:
    cnvpr = find_cnvpr(shape)
    if cnvpr is None:
        return ""
    return (cnvpr.get("descr") or "").strip()


def set_alt_text(shape, text: str) -> None:
    cnvpr = find_cnvpr(shape)
    if cnvpr is not None:
        cnvpr.set("descr", xml_safe_text(text))


def is_meaningful_alt_text(text: str) -> bool:
    """True if ``text`` is non-empty and not just a bare image filename."""
    text = (text or "").strip()
    if not text:
        return False
    return _FILENAME_ALT_RE.match(text) is None


def is_decorative(shape) -> bool:
    """True if the shape carries Microsoft's decorative-image marker."""
    cnvpr = find_cnvpr(shape)
    if cnvpr is None:
        return False
    for dec in cnvpr.iter(f"{{{_NS_ADEC}}}decorative"):
        if dec.get("val") in ("1", "true"):
            return True
    return False


def mark_decorative(shape) -> None:
    """Add the decorative extension so screen readers skip the image.

    Builds::

        <a:extLst><a:ext uri="{...}"><adec:decorative val="1"/></a:ext></a:extLst>

    inside the shape's ``cNvPr`` and clears any alt text (decorative images must
    not have a description).
    """
    cnvpr = find_cnvpr(shape)
    if cnvpr is None:
        return
    cnvpr.set("descr", "")

    ext_lst = cnvpr.find(f"{{{_NS_A}}}extLst")
    if ext_lst is None:
        ext_lst = etree.SubElement(cnvpr, f"{{{_NS_A}}}extLst")

    for ext in ext_lst.findall(f"{{{_NS_A}}}ext"):
        if ext.get("uri") == _DECORATIVE_EXT_URI:
            return  # already marked

    ext = etree.SubElement(ext_lst, f"{{{_NS_A}}}ext")
    ext.set("uri", _DECORATIVE_EXT_URI)
    dec = etree.SubElement(ext, f"{{{_NS_ADEC}}}decorative")
    dec.set("val", "1")
