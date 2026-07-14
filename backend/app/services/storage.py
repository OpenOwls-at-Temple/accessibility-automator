"""Per-user filesystem storage.

Layout (ai_specs/architecture-planning.md):

    <root>/users/<username>/
    ├── input/<group>/<file>          # original — NEVER modified or deleted
    ├── output/<group>/<file>_a11y.<ext> + .report.json / .report.html
    └── metadata.json                 # groups, files, scores, signoffs

Security: every path is built from the **authenticated** username plus a
validated group/filename. Group and file names are restricted to a safe
character set, so a client can never escape its own workspace (no ``..``,
no separators). The engine writes outputs; originals are immutable.
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from remediator.models import FileReport

# Names must start with an alphanumeric, then allow spaces and ``._-``. Spaces
# are safe (not path separators); traversal chars (``..`` ``/`` ``\``) are still
# rejected below. Leading/trailing spaces are stripped before matching.
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]*$")
ALLOWED_EXTENSIONS = {".pptx", ".pdf"}

# The suffix appended to remediated output filenames (``lecture1_<suffix>.pptx``).
# Per-user, editable in Settings. Must be a safe filename token (no spaces or
# separators) so it can never alter the output path.
DEFAULT_SUFFIX = "a11y"
_SUFFIX_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$")


class StorageError(Exception):
    """Invalid name or path — surfaced to the client as a 4xx."""


def _validate(name: str, kind: str) -> str:
    name = (name or "").strip()
    if not _SAFE_NAME.match(name) or ".." in name or "/" in name or "\\" in name:
        raise StorageError(f"Invalid {kind}: {name!r}")
    return name


def a11y_name(filename: str, suffix: str = DEFAULT_SUFFIX) -> str:
    """`lecture1.pptx` -> `lecture1_a11y.pptx` (suffix configurable per user)."""
    stem, _, ext = filename.rpartition(".")
    return f"{stem}_{suffix}.{ext}"


@dataclass
class FileEntry:
    name: str
    file_type: str
    has_output: bool
    pre_fix_score: int | None = None
    post_fix_score: int | None = None
    truly_remediated_score: int | None = None
    status: str = "uploaded"  # uploaded | complete | error


class StorageService:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    # ── workspace paths ──

    def user_dir(self, username: str) -> Path:
        return self.root / "users" / _validate(username, "username")

    def ensure_workspace(self, username: str) -> Path:
        base = self.user_dir(username)
        (base / "input").mkdir(parents=True, exist_ok=True)
        (base / "output").mkdir(parents=True, exist_ok=True)
        if not (base / "metadata.json").exists():
            self._write_metadata(username, {"user": username, "groups": [], "signoffs": []})
        return base

    def input_path(self, username: str, group: str, filename: str) -> Path:
        return (
            self.user_dir(username)
            / "input"
            / _validate(group, "group")
            / _validate(filename, "filename")
        )

    def _output_dir(self, username: str, group: str) -> Path:
        return self.user_dir(username) / "output" / _validate(group, "group")

    def _output_basename(self, username: str, group: str, filename: str, *, for_write: bool) -> str:
        """Resolve a remediated file's basename.

        For a *write* (a fresh Fix run) use the user's current suffix. For a
        *read* (download/listing) prefer the name actually recorded when the
        file was remediated, so changing the suffix never orphans old outputs;
        fall back to the historical default for files fixed before this feature.
        """
        filename = _validate(filename, "filename")
        if for_write:
            return a11y_name(filename, self.get_user_settings(username)["filename_suffix"])
        entry = self._file_entry(username, group, filename)
        if entry and entry.get("output_name"):
            return entry["output_name"]
        return a11y_name(filename)

    def output_path(self, username: str, group: str, filename: str) -> Path:
        """Path to READ an existing remediated output (stored name, else legacy)."""
        return self._output_dir(username, group) / self._output_basename(
            username, group, filename, for_write=False
        )

    def output_write_path(self, username: str, group: str, filename: str) -> Path:
        """Path to WRITE a new remediated output, using the user's current suffix."""
        return self._output_dir(username, group) / self._output_basename(
            username, group, filename, for_write=True
        )

    def report_path(self, username: str, group: str, filename: str, kind: str = "json") -> Path:
        out = self.output_path(username, group, filename)
        return out.with_name(out.name + f".report.{kind}")

    def report_write_path(
        self, username: str, group: str, filename: str, kind: str = "json"
    ) -> Path:
        out = self.output_write_path(username, group, filename)
        return out.with_name(out.name + f".report.{kind}")

    # ── uploads ──

    def save_upload(self, username: str, group: str, filename: str, data: bytes) -> Path:
        filename = _validate(filename, "filename")
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise StorageError(f"Unsupported file type {ext!r}. Allowed: .pptx, .pdf")
        self.ensure_workspace(username)
        dest = self.input_path(username, group, filename)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        self._add_file_entry(username, group, filename, ext.lstrip("."))
        return dest

    # ── listing ──

    def list_groups(self, username: str) -> list[str]:
        input_root = self.user_dir(username) / "input"
        if not input_root.exists():
            return []
        return sorted(p.name for p in input_root.iterdir() if p.is_dir())

    def list_group_files(self, username: str, group: str) -> list[FileEntry]:
        group = _validate(group, "group")
        input_dir = self.user_dir(username) / "input" / group
        if not input_dir.exists():
            return []
        meta_files = {
            f["name"]: f
            for g in self._read_metadata(username).get("groups", [])
            if g["name"] == group
            for f in g.get("files", [])
        }
        entries = []
        for path in sorted(input_dir.iterdir()):
            if not path.is_file():
                continue
            meta = meta_files.get(path.name, {})
            entries.append(
                FileEntry(
                    name=path.name,
                    file_type=path.suffix.lstrip(".").lower(),
                    has_output=self.output_path(username, group, path.name).exists(),
                    pre_fix_score=meta.get("pre_fix_score"),
                    post_fix_score=meta.get("post_fix_score"),
                    truly_remediated_score=meta.get("truly_remediated_score"),
                    status=meta.get("status", "uploaded"),
                )
            )
        return entries

    # ── metadata ──

    def get_metadata(self, username: str) -> dict:
        return self._read_metadata(username)

    # ── per-user settings ──

    def get_user_settings(self, username: str) -> dict:
        settings = self._read_metadata(username).get("settings") or {}
        return {"filename_suffix": settings.get("filename_suffix") or DEFAULT_SUFFIX}

    def set_filename_suffix(self, username: str, suffix: str) -> str:
        suffix = (suffix or "").strip()
        if not _SUFFIX_RE.match(suffix):
            raise StorageError(
                f"Invalid filename suffix: {suffix!r}. Use letters, digits, '.', '_' or '-'."
            )
        self.ensure_workspace(username)
        meta = self._read_metadata(username)
        meta.setdefault("settings", {})["filename_suffix"] = suffix
        self._write_metadata(username, meta)
        return suffix

    def _file_entry(self, username: str, group: str, filename: str) -> dict | None:
        for g in self._read_metadata(username).get("groups", []):
            if g["name"] == group:
                for f in g.get("files", []):
                    if f["name"] == filename:
                        return f
        return None

    def _read_metadata(self, username: str) -> dict:
        path = self.user_dir(username) / "metadata.json"
        if not path.exists():
            return {"user": username, "groups": [], "signoffs": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_metadata(self, username: str, data: dict) -> None:
        base = self.user_dir(username)
        base.mkdir(parents=True, exist_ok=True)
        # Atomic write so concurrent readers never see a half-written file.
        fd, tmp = tempfile.mkstemp(dir=str(base), suffix=".tmp")
        with open(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        Path(tmp).replace(base / "metadata.json")

    def _group_block(self, meta: dict, group: str) -> dict:
        for g in meta["groups"]:
            if g["name"] == group:
                return g
        block = {"name": group, "files": []}
        meta["groups"].append(block)
        return block

    def _add_file_entry(self, username: str, group: str, filename: str, file_type: str) -> None:
        meta = self._read_metadata(username)
        block = self._group_block(meta, group)
        if not any(f["name"] == filename for f in block["files"]):
            block["files"].append({"name": filename, "file_type": file_type, "status": "uploaded"})
        self._write_metadata(username, meta)

    def update_file_scores(
        self,
        username: str,
        group: str,
        filename: str,
        report: FileReport,
        output_name: str | None = None,
    ) -> None:
        meta = self._read_metadata(username)
        block = self._group_block(meta, group)
        for f in block["files"]:
            if f["name"] == filename:
                f.update(
                    pre_fix_score=report.pre_fix_score,
                    post_fix_score=report.post_fix_score,
                    truly_remediated_score=report.truly_remediated_score,
                    status="complete",
                )
                # Remember the exact output name so a later suffix change never
                # orphans this file's download.
                if output_name:
                    f["output_name"] = output_name
                break
        for fix in report.placeholder_fixes:
            meta["signoffs"].append(
                {
                    "group": group,
                    "file": filename,
                    "check_id": fix.check_id,
                    "element_ref": fix.element_ref,
                    "status": "placeholder",
                    "acknowledged_at": None,
                    "note": None,
                }
            )
        self._write_metadata(username, meta)

    def set_file_status(self, username: str, group: str, filename: str, status: str) -> None:
        meta = self._read_metadata(username)
        block = self._group_block(meta, group)
        for f in block["files"]:
            if f["name"] == filename:
                f["status"] = status
                break
        self._write_metadata(username, meta)

    def acknowledge_signoff(
        self, username: str, group: str, filename: str, check_id: str, note: str | None
    ) -> bool:
        from datetime import datetime, timezone

        meta = self._read_metadata(username)
        found = False
        timestamp = datetime.now(timezone.utc).isoformat()
        for s in meta.get("signoffs", []):
            if s["group"] == group and s["file"] == filename and s["check_id"] == check_id:
                s["status"] = "acknowledged"
                s["acknowledged_at"] = timestamp
                s["note"] = note
                found = True
        if found:
            self._write_metadata(username, meta)
        return found
