# Frontend

React 18 + Vite SPA for Accessibility Automator. Talks to the FastAPI backend
with a **JWT bearer token** (kept in `localStorage`, sent as `Authorization`).

```bash
cp .env.example .env     # VITE_API_BASE_URL + VITE_GOOGLE_CLIENT_ID
npm install
npm run dev              # http://localhost:5173
npm run build            # production build -> dist/
npm test                 # Vitest
npm run lint             # ESLint
```

`VITE_GOOGLE_CLIENT_ID` is the Google OAuth **web** client ID (same value as the
backend `GOOGLE_CLIENT_ID`). Leave it blank locally to use the **dev-login** box
instead of the Google button.

## Structure

```
src/
├── components/   # SignInForm (Google + dev login), TopPanel, FileExplorer, UploadModal, ReportViewer
├── pages/        # HomePage, ReportPage, AdminUsers (admin-only invite allowlist)
├── hooks/        # useAuth (JWT session context), useJobStatus (polling)
├── services/     # api.js — backend client (bearer token, authed downloads)
└── utils/        # score.js — Panorama colour bands
```

Flow: sign in (Google SSO, or dev-login locally) → workspace home (top panel +
file explorer) → upload into a group → **Fix** → live job progress → report
(genuine fixes vs placeholders vs manual) with placeholder sign-off → download the
`_a11y` output. Admins also get a **Manage users** page to invite Temple accounts.

> Access is **invite-only** — an admin must add your Temple account first. The
> backend must be running and its `CORS_ORIGINS` must include this origin
> (`http://localhost:5173`, the default).
