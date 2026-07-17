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

Managed with **uv** (`pyproject.toml` + `uv.lock`; no `requirements.txt`).

## Quick start (engine + CLI)

```bash
uv sync                       # install into .venv from the lockfile

# Remediate a PPTX (writes <name>_a11y.pptx + JSON/HTML reports next to it).
uv run python -m backend.cli fix path/to/lecture1.pptx

# Run the tests.
uv run pytest
```

The CLI reads `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` for AI alt text and
slide titles. With none set it still runs, degrading those items to flagged
placeholders. The report surfaces **two** scores — checker-passing vs truly
remediated — so placeholders are never presented as genuine fixes.

## Run the whole app (backend + frontend)

```bash
cp .env.example .env                 # blank GOOGLE_CLIENT_ID -> dev-login works
cp frontend/.env.example frontend/.env
./run_server.sh --setup --admin-email you@temple.edu   # run_server.ps1 on Windows
```

`--setup` installs deps, runs the DB migration (`alembic upgrade head`), and seeds
your admin account, then starts the API (`http://localhost:8000`) and the web UI
(`http://localhost:5173`). Sign in via the **Local dev login** box with the seeded
email. Then: upload a group of files → **Fix** → watch progress → open the report →
download the remediated output. Admins can invite Temple users from **Manage users**.

> Auth is **Google SSO + an admin-managed invite allowlist** (JWT bearer). In
> production set `GOOGLE_CLIENT_ID` / `VITE_GOOGLE_CLIENT_ID` to a Google OAuth web
> client ID; locally the dev-login box stands in. Interactive API docs at `/docs`.

## Status

Phase 1 feature-complete. PPTX path end-to-end (P1–P13). PDF path: metadata
fixes (D2 title, D12 language) with honest detection/reporting of the structural
checks (D1/D3/D8/D9–D11/D16). FastAPI backend (Google SSO + invite-only allowlist,
per-user storage, background jobs) and a React UI wired to it. Deferred: PDF OCR +
structure-tree synthesis — see [`progress.md`](progress.md).
