"""Report generation: JSON (machine-readable) + HTML (human-readable).

The report is deliberately honest (domain-knowledge.md): it shows both the
checker-passing score and the truly-remediated score, and lists placeholder
items in their own "needs human follow-up" section, separate from genuine fixes.
"""

from __future__ import annotations

import html
import json
from dataclasses import asdict
from pathlib import Path

from remediator.models import ACTION_NOT_FIXED, ACTION_PLACEHOLDER, FileReport


def report_to_dict(report: FileReport) -> dict:
    return {
        "file_name": report.file_name,
        "file_type": report.file_type,
        "scores": {
            "pre_fix": report.pre_fix.as_dict() if report.pre_fix else None,
            "post_fix_checker_passing": report.post_fix.as_dict() if report.post_fix else None,
            "truly_remediated": (
                report.truly_remediated.as_dict() if report.truly_remediated else None
            ),
        },
        "fixes": [asdict(f) for f in report.fixes],
        "pre_fix_audit": [asdict(a) for a in report.pre_fix_audit],
        "post_fix_audit": [asdict(a) for a in report.post_fix_audit],
    }


def write_json_report(report: FileReport, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report_to_dict(report), indent=2), encoding="utf-8")
    return path


def _rows(fixes) -> str:
    return "".join(
        f"<tr><td>{html.escape(f.check_id)}</td>"
        f"<td>{html.escape(f.element_ref)}</td>"
        f"<td>{html.escape(f.detail)}</td></tr>"
        for f in fixes
    )


def render_html_report(report: FileReport) -> str:
    genuine = [f for f in report.fixes if f.action not in (ACTION_PLACEHOLDER, ACTION_NOT_FIXED)]
    placeholders = [f for f in report.fixes if f.action == ACTION_PLACEHOLDER]
    needs_manual = [f for f in report.fixes if f.action == ACTION_NOT_FIXED]

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Accessibility Report — {html.escape(report.file_name)}</title>
<style>
 body {{ font-family: system-ui, sans-serif; max-width: 880px; margin: 2rem auto; color:#1a2235; }}
 h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1.1rem; margin-top: 2rem; }}
 .scores {{ display:flex; gap:1.5rem; margin:1rem 0; }}
 .score {{ border:1px solid #ddd; border-radius:8px; padding:1rem 1.4rem; text-align:center; }}
 .score b {{ display:block; font-size:1.8rem; }}
 table {{ width:100%; border-collapse:collapse; font-size:.9rem; }}
 th,td {{ text-align:left; padding:.4rem .6rem; border-bottom:1px solid #eee; vertical-align:top; }}
 .muted {{ color:#667; }}
</style></head><body>
<h1>Accessibility Report — {html.escape(report.file_name)}</h1>
<div class="scores">
  <div class="score"><b>{report.pre_fix_score}</b>Before</div>
  <div class="score"><b>{report.post_fix_score}</b>After (checker-passing)</div>
  <div class="score"><b>{report.truly_remediated_score}</b>Truly remediated</div>
</div>
<p class="muted">The gap between "checker-passing" and "truly remediated" is the
work that still needs a human. The real score is confirmed on re-upload to Canvas.</p>

<h2>Genuinely fixed ({len(genuine)})</h2>
<table><tr><th>Check</th><th>Element</th><th>Detail</th></tr>{_rows(genuine)}</table>

<h2>Needs human follow-up — placeholders ({len(placeholders)})</h2>
<table><tr><th>Check</th><th>Element</th><th>Detail</th></tr>{_rows(placeholders)}</table>

<h2>Needs manual fix — report only ({len(needs_manual)})</h2>
<table><tr><th>Check</th><th>Element</th><th>Detail</th></tr>{_rows(needs_manual)}</table>
</body></html>
"""


def write_html_report(report: FileReport, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html_report(report), encoding="utf-8")
    return path
