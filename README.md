# Accessibility Automator

Remediates Temple faculty lecture files (PowerPoint in Phase 1, PDF next) against
WCAG so they score near-100 when re-uploaded to Canvas / YuJa Panorama. Built with
the **OpenOwls SDD** process — see [`docs/getting-started.html`](docs/getting-started.html)
and the specs in [`ai_specs/`](ai_specs/).

## Layout

| Path | What it is |
|------|------------|
| `remediator/` | The engine: audit → fix → re-score → report. Standalone; never imports `backend/`. |
| `backend/` | FastAPI web layer (CLI built; API next). May import `remediator/`. |
| `frontend/` | React + Vite SPA (not started yet). |
| `ai_specs/` | The SDD spec set (source of truth). |
| `config.yaml` | Non-secret runtime config. Secrets live in env vars (`.env.example`). |

## Quick start (engine + CLI)

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Remediate a PPTX (writes <name>_a11y.pptx + JSON/HTML reports next to it).
python -m backend.cli fix path/to/lecture1.pptx

# Run the tests.
pytest
```

The CLI reads `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` for AI alt text and
slide titles. With none set it still runs, degrading those items to flagged
placeholders. The report surfaces **two** scores — checker-passing vs truly
remediated — so placeholders are never presented as genuine fixes.

## Status

Phase 1. PPTX path complete end-to-end (P1–P13). PDF path complete for metadata
fixes (D2 title, D12 language) with honest detection/reporting of the structural
checks (D1/D3/D8/D9–D11/D16); PDF OCR and structure-tree synthesis are deferred
follow-ups. The FastAPI app and React UI are next — see [`progress.md`](progress.md).
