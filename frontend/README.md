# Frontend (not started)

React 18 + Vite SPA for Accessibility Automator. Per the implementation order in
`ai_specs/architecture-planning.md`, the UI is built **after** the engine and the
FastAPI backend. Planned structure:

```
frontend/
├── src/
│   ├── components/   # FileExplorer, UploadModal, ReportViewer, SignOffModal
│   ├── pages/        # HomePage, GroupPage, ReportPage
│   ├── hooks/        # useAuth, useJobStatus (polling)
│   ├── services/     # API client
│   └── utils/
├── tests/
└── public/
```

Flow: sign in → file-explorer home → upload into a group → **Fix** → poll job
status → view before/after report → download `_a11y` files.
