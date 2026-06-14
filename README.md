# Accessibility Automator

Remediates Temple faculty lecture files (PowerPoint in Phase 1, PDF next) against
WCAG so they score near-100 when re-uploaded to Canvas / YuJa Panorama. Built with
the **OpenOwls SDD** process — see [`docs/getting-started.html`](docs/getting-started.html)
and the specs in [`ai_specs/`](ai_specs/).

## Layout

| Path | What it is |
|------|------------|
| `remediator/` | The engine: audit → fix → re-score → report. Standalone; never imports `backend/`. |
| `backend/` | FastAPI web layer (`app/`) + CLI. May import `remediator/`. |
| `frontend/` | React + Vite SPA (sign-in, file explorer, Fix, report viewer). |
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

## Run the API server

```bash
cp .env.example .env          # AUTH_PROVIDER=mock for local dev
uvicorn backend.app.main:app --reload    # http://localhost:8000
```

With `AUTH_PROVIDER=mock`, `POST /api/v1/auth/login {"email": "..."}` signs you
in (a signed-cookie session) and creates your workspace. Flow: upload files into
a group → `POST /api/v1/groups/{group}/remediate` (background job) → poll
`GET /api/v1/jobs/{id}` → read the report and download the `_a11y` output.
Interactive docs at `/docs`.

## Run the web UI

```bash
cd frontend
cp .env.example .env          # VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev                   # http://localhost:5173
```

Sign in with any email (mock auth), upload a group of files, click **Fix**, watch
progress, then open the report and download the remediated output.

## Status

Phase 1 feature-complete. PPTX path end-to-end (P1–P13). PDF path: metadata
fixes (D2 title, D12 language) with honest detection/reporting of the structural
checks (D1/D3/D8/D9–D11/D16). FastAPI backend (mock auth, per-user storage,
background jobs) and a React UI wired to it. Deferred: PDF OCR + structure-tree
synthesis, real Azure/Temple SSO — see [`progress.md`](progress.md).
