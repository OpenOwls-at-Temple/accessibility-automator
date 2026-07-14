# Contributing

Developer setup and workflow for **Accessibility Automator**. For the *why* behind
the design, read the specs in [`ai_specs/`](ai_specs/) (start with `overview.md`
and `conventions.md`); this file is the *how*.

## Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)** (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Node.js 20+**
- **Tesseract** — only for the (still-deferred) scanned-PDF OCR path; skip it otherwise
  (`brew install tesseract` / `apt-get install tesseract-ocr`).

## First-time setup

A fresh clone has **no `.env` and no database** (both are gitignored). Because
sign-in is **invite-only**, you also start with **zero users** — so the first
thing you do is seed *yourself* as an admin.

```bash
git clone <repo-url>
cd accessibility-automator

cp .env.example .env                 # leave GOOGLE_CLIENT_ID blank -> dev-login works
cp frontend/.env.example frontend/.env

# Installs deps, creates the DB (alembic), seeds YOU as admin, starts both servers:
./run_server.sh --setup --admin-email you@temple.edu     # run_server.ps1 on Windows
```

`--setup` runs `uv sync` → `uv run alembic upgrade head` (creates `a11y.db` + the
`users` table) → seeds `you@temple.edu` as admin → `npm install`. Then it serves the
API on http://localhost:8000 and the web app on http://localhost:5173.

Prefer to do it by hand?

```bash
uv sync
uv run alembic upgrade head
uv run python -m backend.app.seed --admin you@temple.edu
uv run uvicorn backend.app.main:app --reload      # terminal 1
cd frontend && npm install && npm run dev          # terminal 2
```

## Signing in locally

Open http://localhost:5173. With `GOOGLE_CLIENT_ID` blank you'll see a "Google
sign-in is not configured" note and a **Local dev login** box underneath — use it
with the email you seeded (`you@temple.edu`).

- The dev-login is **not** "any email": it requires an email that is **registered
  and active** in your local DB. It just skips Google's identity check, and it is
  **disabled entirely when `ENVIRONMENT != local`**.
- As an admin you get a **Manage users** page — invite more emails there (they get
  added to *your* local `a11y.db`).
- Each developer has their **own** local `a11y.db` — it is never committed or
  shared. Delete it and re-run `--setup` to reset.

To exercise the **real** Google button, set `GOOGLE_CLIENT_ID` (backend `.env`) and
`VITE_GOOGLE_CLIENT_ID` (`frontend/.env`) to a Google OAuth **web** client ID, and
add `http://localhost:5173` to that client's Authorized JavaScript origins. See
[`ai_specs/deployment.md`](ai_specs/deployment.md).

### macOS + OneDrive venv note

This repo lives in a OneDrive folder shared between macOS and Windows, so the
in-repo `.venv/` may be the *other* OS's. `uv run` self-heals the venv per-OS. If
you keep a manual Mac venv (e.g. `~/.venvs/accessibility-automator`), activate it
and pass `--no-uv` to `run_server.sh` to use it directly.

## Project layout

| Path | What it is |
|------|------------|
| `remediator/` | The engine: audit → fix → re-score → report. **Never imports `backend/`** — one-way dependency, also runnable via the CLI. |
| `backend/` | FastAPI web layer (`app/`) + CLI. May import `remediator/`. Auth/allowlist DB lives here. |
| `frontend/` | React + Vite SPA. |
| `alembic/` | User-allowlist DB migrations (run from the repo root). |
| `ai_specs/` | The SDD spec set — **source of truth**. Don't edit without explicit sign-off. |

## Everyday commands

```bash
# Python (from repo root)
uv run pytest                         # backend + engine tests
uv run black backend alembic remediator      # format
uv run ruff check backend alembic remediator # lint

# Frontend (from frontend/)
npm test        # Vitest
npm run lint    # ESLint
npm run build   # production build
```

## Adding dependencies

- **Python:** add to `pyproject.toml` (`[project.dependencies]` for runtime,
  `[dependency-groups] dev` for tooling) and commit the updated **`uv.lock`**
  (`uv lock`). There is **no `requirements.txt`**.
- **Frontend:** `npm install <pkg>` and commit `package-lock.json`.

## Database changes

The `users` allowlist is the only DB. Schema changes go through an **Alembic
migration** — never `create_all` at startup:

```bash
uv run alembic revision -m "describe change"   # then edit the generated file
uv run alembic upgrade head
```

Keep migrations additive / backward-compatible.

## Conventions & Git workflow

- Follow [`ai_specs/conventions.md`](ai_specs/conventions.md) (naming, the one-way
  engine dependency, LLM rules, the invite-only/no-auto-provision auth rules).
- Commit style: `type: short description` (`feat`, `fix`, `docs`, `refactor`,
  `test`, `chore`).
- Every change on its own `type/short-description` branch — no direct commits to
  `main`. Open a PR; **CI (black/ruff/pytest + frontend lint/test/build) must pass**
  and at least one review is required before merge.
- After finishing a meaningful unit of work, update [`progress.md`](progress.md).
