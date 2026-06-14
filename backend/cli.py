"""Thin CLI over the remediation engine.

Lets the engine run end-to-end without the web layer:

    python -m backend.cli fix path/to/lecture1.pptx
    python -m backend.cli fix lecture1.pptx --output out/lecture1_a11y.pptx

Reads ``LLM_*`` env vars for AI alt text/titles; with none set it still runs and
degrades unfixable items to placeholders.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from remediator.config import load_config
from remediator.models import ACTION_AI_FIXED, ACTION_AUTO_FIXED, ACTION_NOT_FIXED
from remediator.pipeline import remediate_file
from remediator.reporter import write_html_report, write_json_report


def _default_output(input_path: Path) -> Path:
    """`lecture1.pptx` -> `lecture1_a11y.pptx` (the project naming convention)."""
    return input_path.with_name(f"{input_path.stem}_a11y{input_path.suffix}")


def _cmd_fix(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: file not found: {input_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else _default_output(input_path)
    cfg = load_config(args.config)

    report = remediate_file(input_path, output_path, cfg=cfg)

    json_path = write_json_report(report, f"{output_path}.report.json")
    html_path = write_html_report(report, f"{output_path}.report.html")

    genuine = sum(1 for f in report.fixes if f.action in (ACTION_AUTO_FIXED, ACTION_AI_FIXED))
    needs_manual = sum(1 for f in report.fixes if f.action == ACTION_NOT_FIXED)

    print(f"Remediated: {input_path.name} -> {output_path}")
    print(f"  Score before:               {report.pre_fix_score}")
    print(f"  Score after (checker):      {report.post_fix_score}")
    print(f"  Score truly remediated:     {report.truly_remediated_score}")
    print(f"  Genuine fixes:              {genuine}")
    print(f"  Placeholders (follow-up):   {len(report.placeholder_fixes)}")
    print(f"  Needs manual fix:           {needs_manual}")
    print(f"  Reports: {json_path.name}, {html_path.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="backend.cli", description="Accessibility Automator CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    fix = sub.add_parser("fix", help="Remediate a single file")
    fix.add_argument("input", help="Path to the input file (.pptx or .pdf)")
    fix.add_argument("-o", "--output", help="Output path (default: <name>_a11y.<ext>)")
    fix.add_argument("-c", "--config", help="Path to config.yaml")
    fix.set_defaults(func=_cmd_fix)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
