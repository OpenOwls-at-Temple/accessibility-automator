# Frontend

React 18 + Vite SPA for Accessibility Automator. Talks to the FastAPI backend
with cookie auth (`credentials: "include"`).

```bash
cp .env.example .env     # VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev              # http://localhost:5173
npm run build            # production build -> dist/
npm test                 # Vitest
npm run lint             # ESLint
```

## Structure

```
src/
├── components/   # SignInForm, TopPanel, FileExplorer, UploadModal, ReportViewer
├── pages/        # HomePage, ReportPage
├── hooks/        # useAuth (session context), useJobStatus (polling)
├── services/     # api.js — backend client
└── utils/        # score.js — Panorama colour bands
```

Flow: sign in (mock: any email) → workspace home (top panel + file explorer) →
upload into a group → **Fix** → live job progress → report (genuine fixes vs
placeholders vs manual) with placeholder sign-off → download the `_a11y` output.

> The backend must be running and its `CORS_ORIGINS` must include this origin
> (`http://localhost:5173`, the default).
