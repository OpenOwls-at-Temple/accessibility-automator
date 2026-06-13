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

Primary target is **Render** for Phase 1, with the **Temple data center** as the alternative if access and approval are obtained. There is **no database** to provision.

| Component | Platform | Notes |
|-----------|----------|-------|
| Frontend | Render Static Site (Vite build output `frontend/dist`) | Auto-deploys from `main` |
| Backend | Render Web Service (Docker, FastAPI) | Tesseract installed in the image for OCR; free tier spins down after inactivity |
| File storage | Render **Persistent Disk** mounted at `STORAGE_DIR` | Per-user workspaces live here; **must be a persistent disk, not ephemeral**, or files are lost on redeploy |
| LLM | External OpenAI-compatible endpoint | Configured via env vars; provider swappable |
| Auth (prod) | Microsoft Azure AD / Temple SSO | Requires Temple IT app registration |

---

## Environment Variables
<!-- Never put actual values here. Keep a .env.example with dummy values. -->

### Backend
| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_KEY` | Yes | API key for the OpenAI-compatible LLM endpoint |
| `LLM_BASE_URL` | Yes | Base URL of the LLM endpoint (enables provider swap) |
| `LLM_MODEL` | Yes | Vision-capable model name |
| `AUTH_PROVIDER` | Yes | `mock` (local/dev) or `azure` (production) |
| `AZURE_CLIENT_ID` | Prod | Azure AD app (client) ID |
| `AZURE_CLIENT_SECRET` | Prod | Azure AD client secret |
| `AZURE_TENANT_ID` | Prod | Temple tenant ID (restricts sign-in to Temple) |
| `AZURE_REDIRECT_URI` | Prod | OAuth2 redirect URI registered with Azure |
| `SESSION_SECRET` | Yes | Secret for signing the session cookie / JWT |
| `STORAGE_DIR` | Yes | Root directory for per-user workspaces (mount a persistent disk here in prod) |
| `CORS_ORIGINS` | Yes | Allowed frontend origin(s) |
| `ENVIRONMENT` | Yes | `local` or `production` |

### Frontend
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Base URL of the backend API |

> ⚠️ Never commit `.env` files. Add them to `.gitignore` and keep a checked-in `.env.example` with dummy values.

---

## Local Development Setup
<!-- Step-by-step instructions to run the project locally from scratch. -->

### Prerequisites
- Node.js 20+
- Python 3.11+
- **Tesseract OCR** (required for scanned-PDF handling): `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- An API key for an OpenAI-compatible vision model endpoint

### Steps

```bash
# 1. Clone
git clone [repo-url]
cd accessibility-automator

# 2. Backend
cd backend
cp .env.example .env          # set AUTH_PROVIDER=mock locally; fill LLM_* values
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # http://localhost:8000

# 3. Frontend (new terminal)
cd frontend
cp .env.example .env          # set VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev                   # http://localhost:5173

# 4. (Optional) Run the engine directly without the web layer
python -m backend.cli fix path/to/lecture1.pptx
```

Locally, `AUTH_PROVIDER=mock` lets you sign in by entering an email — no Azure setup needed.

---

## Deployment Process

### Frontend (Render Static Site)
1. Build command `npm run build`, publish directory `frontend/dist`.
2. Set `VITE_API_BASE_URL` to the backend service URL.
3. Auto-deploys on push to `main`.

### Backend (Render Web Service, Docker)
1. Dockerfile installs Tesseract and Python deps, runs `uvicorn`.
2. Set all backend env vars in the Render dashboard (`AUTH_PROVIDER=azure` in prod).
3. Attach a **Persistent Disk** mounted at `STORAGE_DIR` (e.g. `/data`).
4. First deploy may take several minutes.

### Azure SSO (one-time, prod)
1. Register the app in Temple's Azure AD tenant (Temple IT).
2. Add `AZURE_REDIRECT_URI` to the app's allowed redirect URIs.
3. Set `AZURE_CLIENT_ID/SECRET/TENANT_ID` in Render. Until this is done, the app runs with `AUTH_PROVIDER=mock`.

---

## CI/CD Pipeline

GitHub Actions on every pull request:
- Lint (`black --check`, `ruff`, `eslint`)
- Tests (`pytest`, frontend tests)
- Frontend build check

Merging to `main` triggers Render auto-deploy. Production cutover (switching to `azure` auth) requires faculty approval.

---

## Common Deployment Issues
<!-- Document problems the team encounters and how to fix them. -->

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Uploaded/remediated files disappear after redeploy | Storage on ephemeral disk | Mount a **persistent disk** at `STORAGE_DIR` |
| OCR step fails on scanned PDFs | Tesseract not installed in the image | Add Tesseract to the Dockerfile |
| SSO login loops or errors | Redirect URI mismatch | Ensure `AZURE_REDIRECT_URI` exactly matches the value registered in Azure |
| Frontend can't reach backend | Wrong `VITE_API_BASE_URL` or CORS | Fix the URL; add the frontend origin to `CORS_ORIGINS` |
| Backend 500 on first request | Missing env var | Check Render logs; verify all required vars are set |
| Large files rejected | Exceeds `storage.max_file_size_mb` | Adjust config or inform the user |

---

## Secrets Management

- All secrets live in the hosting platform's environment variable settings — never in code or committed files.
- Rotate `LLM_API_KEY`, `AZURE_CLIENT_SECRET`, and `SESSION_SECRET` immediately if ever exposed.
- Local development uses each student's own LLM API key and `AUTH_PROVIDER=mock`.
- Per the project's privacy stance: only faculty course materials are processed; no student data is stored, and the LLM provider should be one that does not train on inputs (confirm and record the provider's policy).
