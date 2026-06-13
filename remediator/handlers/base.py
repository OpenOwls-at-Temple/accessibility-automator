"""The :class:`FormatHandler` interface.

A handler owns the lifecycle of one open document — opening it, exposing the
underlying library object (a ``python-pptx`` ``Presentation``, a ``pikepdf.Pdf``,
...), and saving it back. Format-specific audit and fix logic lives in the
``rules/`` and ``fixers/`` modules, which operate on the object a handler exposes.

Adding a new format (Word, etc. in Phase 2) means adding a handler plus a rules
and fixer module — the pipeline, scorer, and reporter do not change.
"""

from __future__ import annotations

import abc
from pathlib import Path


class FormatHandler(abc.ABC):
    file_type: str = ""  # "pptx" | "pdf" | ...

    def __init__(self, path: str | Path):
        self.path = Path(path)

    @abc.abstractmethod
    def save(self, output_path: str | Path) -> None:
        """Write the (possibly modified) document to ``output_path``."""

    @classmethod
    def supported_extensions(cls) -> tuple[str, ...]:
        """Lowercase file extensions (with dot) this handler can open."""
        return ()
