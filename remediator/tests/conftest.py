"""Shared test fixtures: programmatically built known-bad / known-good PPTX
files (so no binaries live in git) plus a fake LLM provider.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image
from pptx import Presentation
from pptx.util import Inches

from remediator.handlers.pptx_handler import set_alt_text
from remediator.llm.provider import CaptionResult, TitleResult


def _png_bytes() -> io.BytesIO:
    img = Image.new("RGB", (64, 64), (120, 160, 200))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


def _set_lang(run, lang="en-US") -> None:
    run._r.get_or_add_rPr().set("lang", lang)


@pytest.fixture
def png_bytes() -> bytes:
    return _png_bytes().getvalue()


@pytest.fixture
def bad_pptx(tmp_path):
    """A deck that fails P1, P2, P3, P5, P6."""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title + Content
    # P2: leave the title placeholder empty, but give the slide body text.
    slide.placeholders[1].text = "Light reactions occur in the thylakoid membrane."
    # P3: image with no alt text.
    slide.shapes.add_picture(_png_bytes(), Inches(1), Inches(3), Inches(2), Inches(2))
    # P5: table with no header row.
    table = slide.shapes.add_table(2, 2, Inches(4), Inches(3), Inches(4), Inches(1)).table
    table.first_row = False
    table.cell(0, 0).text = "A"
    table.cell(0, 1).text = "B"
    # P1: empty document title. P6: runs carry no language attribute by default.
    prs.core_properties.title = ""
    path = tmp_path / "bad.pptx"
    prs.save(str(path))
    return path


@pytest.fixture
def good_pptx(tmp_path):
    """A fully accessible deck — should score 100."""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Photosynthesis Overview"
    body = slide.placeholders[1]
    body.text = "Light reactions occur in the thylakoid membrane."
    for para in body.text_frame.paragraphs:
        for run in para.runs:
            _set_lang(run)
    for para in slide.shapes.title.text_frame.paragraphs:
        for run in para.runs:
            _set_lang(run)
    pic = slide.shapes.add_picture(_png_bytes(), Inches(1), Inches(3), Inches(2), Inches(2))
    set_alt_text(pic, "Diagram of the light-dependent reactions")
    table = slide.shapes.add_table(2, 2, Inches(4), Inches(3), Inches(4), Inches(1)).table
    table.first_row = True
    prs.core_properties.title = "Biology Lecture 1"
    path = tmp_path / "good.pptx"
    prs.save(str(path))
    return path


class FakeProvider:
    """High-confidence stand-in for the LLM (no network)."""

    def __init__(self, decorative=False):
        self.decorative = decorative

    def caption_image(self, image_bytes, mime_type="image/png", context=""):
        if self.decorative:
            return CaptionResult(alt_text="", decorative=True, confidence=0.9)
        return CaptionResult(alt_text="A blue square test image", decorative=False, confidence=0.9)

    def suggest_title(self, slide_text):
        return TitleResult(title="Light Reactions", confidence=0.9)


@pytest.fixture
def fake_provider():
    return FakeProvider()


@pytest.fixture
def decorative_provider():
    return FakeProvider(decorative=True)
