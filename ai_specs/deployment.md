# Deployment

> **OpenOwls SDD** — Read by engineers and DevOps-minded team members.
> Defines how the application is built, configured, and deployed across environments.
> Claude Code uses this file to understand deployment targets and avoid environment-specific mistakes.

---

## Environments
<!-- Define each environment and its purpose. -->

| Environment | Purpose | URL |
|-------------|---------|-----|
| Local | Development and testing on your own machine | Frontend `http://localhost:5173`, API `http://localhost:8000` |
| Production | Live application for faculty | Render URL (or a Temple-hosted URL if approved) |

A separate staging environment is optional for Phase 1; if used, it is a second Render service.

---

## Hosting Platforms
<!-- Where is each part of the application hosted and why? -->

Primary target is **Render** for Phase 1 (via the checked-in `render.yaml` Blueprint), with the **Temple data center** as the alternative if access and approval are obtained. The only database is the **user allowlist** — **SQLite on the backend's persistent disk** (`sqlite:////data/a11y.db`). Because the app already requires a persistent disk for the document files (which pins it to a single backend instance), the allowlist is a tiny, low-concurrency `users` table, and external Postgres's main benefit — many stateless instances sharing one DB — does not apply, SQLite-on-disk is the chosen prod DB. **Supabase Postgres** remains a supported alternative (set `DATABASE_URL` to the pooler URL) if managed backups/dashboard or a service-independent DB are wanted later.

| Component | Platform | Notes |
|-----------|----------|-------|
| Frontend | Render Static Site (Vite build output `frontend/dist`) | Auto-deploys from `main`; SPA rewrite to `/index.html` |
| Backend | Render Web Service (Python runtime, uv) | `uv sync` build; `alembic upgrade head` then `uvicorn` start. Switch to a Docker runtime when PDF OCR (Tesseract) lands. |
| File storage | Render **Persistent Disk** mounted at `STORAGE_DIR` | Per-user workspaces live here; **must be a persistent disk, not ephemeral**, or files are lost on redeploy |
| Allowlist DB | **SQLite on the persistent disk** (`DATABASE_URL=sqlite:////data/a11y.db`) — or Supabase Postgres | Only the `users` table; Alembic migrates it on each deploy. Lives on the same disk as the documents |
| LLM | External OpenAI-compatible endpoint | Configured via env vars; provider swappable |
| Auth (prod) | **Google SSO** (Google Cloud OAuth web client) + admin allowlist | No Temple IT tenant registration needed — just a Google OAuth client and a seeded admin |

---

## Environment Variables
<!-- Never put actual values here. Keep a .env.example with dummy values. -->

### Backend
| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_KEY` | Yes | API key for the OpenAI-compatible LLM endpoint |
| `LLM_BASE_URL` | Yes | Base URL of the LLM endpoint (enables provider swap) |
| `LLM_MODEL` | Yes | Vision-capable model name |
| `GOOGLE_CLIENT_ID` | Prod | Google OAuth **web** client ID (same value as the frontend). Blank locally → dev-login only. |
| `ALLOWED_EMAIL_DOMAIN` | Yes | Sign-in restricted to this email domain (default `temple.edu`) |
| `JWT_SECRET` | Yes | Secret for signing the app JWT (Render can generate one) |
| `DATABASE_URL` | Yes | User-allowlist DB — SQLite locally (`sqlite:///./a11y.db`) and in prod on the persistent disk (`sqlite:////data/a11y.db`); or a Supabase Postgres pooler URL |
| `STORAGE_DIR` | Yes | Root directory for per-user workspaces (mount a persistent disk here in prod) |
| `FRONTEND_URL` | Yes | Base URL of the frontend (CORS + links) |
| `CORS_ORIGINS` | Yes | Allowed frontend origin(s); defaults to `FRONTEND_URL` |
| `ENVIRONMENT` | Yes | `local` or `production` (`production` disables `/auth/dev-login`) |

### Frontend
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Base URL of the backend API |
| `VITE_GOOGLE_CLIENT_ID` | Prod | Google OAuth web client ID (same value as backend `GOOGLE_CLIENT_ID`) |

> ⚠️ Never commit `.env` files. Add them to `.gitignore` and keep a checked-in `.env.example` with dummy values.

---

## Local Development Setup
<!-- Step-by-step instructions to run the project locally from scratch. -->

### Prerequisites
- Node.js 20+
- Python 3.11+ and **uv** (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Tesseract OCR** (required for scanned-PDF handling): `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- An API key for an OpenAI-compatible vision model endpoint

### Steps

```bash
# 1. Clone
git clone [repo-url]
cd accessibility-automator
cp .env.example .env          # blank GOOGLE_CLIENT_ID -> dev-login; fill LLM_* if desired
cp frontend/.env.example frontend/.env

# 2. One-shot setup + run (installs deps, migrates DB, seeds an admin, starts both)
./run_server.sh --setup --admin-email you@temple.edu     # (run_server.ps1 on Windows)

# --- or do it manually ---
uv sync                                   # install into .venv from uv.lock
uv run alembic upgrade head               # create the users table
uv run python -m backend.app.seed --admin you@temple.edu
uv run uvicorn backend.app.main:app --reload   # http://localhost:8000
# then, in frontend/:  npm install && npm run dev   # http://localhost:5173

# 3. (Optional) Run the engine directly without the web layer
uv run python -m backend.cli fix path/to/lecture1.pptx
```

Locally, leave `GOOGLE_CLIENT_ID` blank and sign in via the **"Local dev login"** box with the seeded admin email — no Google setup needed. On a Mac using a manually-managed venv (e.g. `~/.venvs/accessibility-automator`, since the in-repo `.venv` is the Windows one under OneDrive), activate it and pass `--no-uv` to `run_server.sh`.

---

## Deployment Process

### Render Blueprint (both services)
The repo's `render.yaml` defines both services. In the Render dashboard: **New + → Blueprint**, connect the repo, and Render prompts for every `sync: false` secret.

- **Backend** (`type: web`, python runtime, **`plan: starter`**): build `pip install uv && uv sync --no-dev`; start `uv run alembic upgrade head && uv run uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`; health `/api/v1/health`; a **Persistent Disk** mounted at `/data` with `STORAGE_DIR=/data`. Alembic migrates the allowlist on each deploy. A **paid** instance (Starter+) is required — Render's Free instances get an ephemeral filesystem and cannot attach a disk, so documents and the SQLite allowlist would be wiped on every redeploy/restart. Bump to `standard` if large image-heavy decks exhaust the 512 MB Starter RAM.
- **Frontend** (`type: static`, free): build `npm ci && npm run build`, publish `frontend/dist`, SPA rewrite to `/index.html`. Set `VITE_API_BASE_URL` and `VITE_GOOGLE_CLIENT_ID`.
- **Database**: `DATABASE_URL` is preset in `render.yaml` to `sqlite:////data/a11y.db` — SQLite on the same persistent disk, no external service. (To use Supabase instead, change that var to `sync: false` and paste the pooler URL when prompted.)

### Google SSO (one-time, prod)
1. In **Google Cloud Console → APIs & Services → Credentials**, create an **OAuth 2.0 Client ID** of type **Web application**.
2. Add the frontend origin to **Authorized JavaScript origins** (e.g. `https://<frontend>.onrender.com`).
3. Put the client ID in both `GOOGLE_CLIENT_ID` (backend) and `VITE_GOOGLE_CLIENT_ID` (frontend) — same value. No client *secret* is needed (the frontend uses Google Identity Services and the backend verifies the ID token).
4. **Seed the first admin** so someone can invite others (one-off). With SQLite-on-disk the DB lives on the backend instance, so run the seed **there** via the Render dashboard **Shell** tab: `uv run python -m backend.app.seed --admin you@temple.edu` (it picks up `DATABASE_URL=sqlite:////data/a11y.db` from the service env). That admin then adds Temple users from the in-app **Manage users** page. (With Supabase you could instead run it locally against the pooler URL: `DATABASE_URL=<pooler-url> uv run python -m backend.app.seed --admin you@temple.edu`.)

---

## CI/CD Pipeline

GitHub Actions (`.github/workflows/ci.yml`) on every pull request and push to `main`:
- Backend: `uv sync`, `uv run black --check`, `uv run ruff check`, `uv run pytest`
- Frontend: `npm ci`, `npm run lint`, `npm test`, `npm run build`

Merging to `main` triggers Render auto-deploy. Going live to real users requires setting `GOOGLE_CLIENT_ID`/`VITE_GOOGLE_CLIENT_ID` and seeding an admin.

---

## Common Deployment Issues
<!-- Document problems the team encounters and how to fix them. -->

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Uploaded/remediated files disappear after redeploy | Storage on ephemeral disk | Mount a **persistent disk** at `STORAGE_DIR` |
| OCR step fails on scanned PDFs | Tesseract not installed in the image | Add Tesseract to the Dockerfile |
| Google sign-in button missing or errors | `GOOGLE_CLIENT_ID`/`VITE_GOOGLE_CLIENT_ID` unset or origin not authorized | Set both to the same client ID; add the frontend origin under the OAuth client's Authorized JavaScript origins |
| "Account not registered" on a valid Temple login | Email not in the allowlist | An admin adds it via **Manage users**; seed the first admin with `backend.app.seed` |
| Users/data gone after deploy, or DB errors | Migration didn't run, or SQLite on ephemeral disk | Ensure `alembic upgrade head` runs on deploy; use Supabase or SQLite on the persistent disk |
| Frontend can't reach backend | Wrong `VITE_API_BASE_URL` or CORS | Fix the URL; add the frontend origin to `CORS_ORIGINS` |
| Backend 500 on first request | Missing env var | Check Render logs; verify all required vars are set |
| Large files rejected | Exceeds `storage.max_file_size_mb` | Adjust config or inform the user |

---

## Secrets Management

- All secrets live in the hosting platform's environment variable settings — never in code or committed files.
- Rotate `LLM_API_KEY`, `JWT_SECRET`, and `DATABASE_URL` immediately if ever exposed. (The Google OAuth **web** client ID is not a secret — no client secret is used.)
- Local development uses each student's own LLM API key and the dev-login (blank `GOOGLE_CLIENT_ID`).
- Per the project's privacy stance: only faculty course materials are processed; no student data is stored, and the LLM provider should be one that does not train on inputs (confirm and record the provider's policy).
