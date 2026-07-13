# Progress

> **OpenOwls SDD** — Living status document. Update this file at the end of every work session.
> Claude Code reads this first at the start of every new session to catch up on project state.

## Current Phase
<!-- Which phase are we actively working on? e.g. Phase 1 -->

**Active Phase:** Phase 1 — engine (PPTX + PDF), FastAPI backend, and the React frontend are all in. Phase 1 feature-complete (pending real Azure SSO + PDF OCR follow-ups).

## Status Summary
<!-- One or two sentences describing where the project stands right now -->

Full stack now exists. The `remediator/` engine audits/fixes/re-scores/reports **PPTX (P1–P13) and PDF**; the **FastAPI backend** wraps it (mock auth, per-user storage with path-traversal protection, grouped uploads, background jobs + polling, reports, sign-off); and the **React (Vite) frontend** provides sign-in, the workspace home page (top panel + file explorer), upload, the **Fix** button with live job progress, and a report viewer with placeholder sign-off — all wired to the API with cookie auth. Backend/engine: 41 Python tests pass. Frontend: builds clean, ESLint clean, 4 Vitest tests pass; dev server serves the app. **Not yet done:** a full in-browser click-through (build/lint/unit verified, but no headless-browser E2E yet). **Deferred follow-ups:** PDF OCR (D8), PDF structure-tree/alt-text (D1/D3), real Azure/Temple SSO.

---

## Integration / Branch State
<!-- Where the code actually lives across branches and PRs. -->

✅ **`main` is complete — the full Phase 1 stack is on `main`.** The stacked PRs #1–#4
originally merged into their intermediate base branches (not up to `main`), so a
follow-up **PR #5** (`feature/react-frontend` → `main`) was opened and **merged** to land
PDF + backend + frontend in one go. Verified on `main`: 41 Python + 4 frontend tests pass,
`vite build` clean.

| PR | Scope | State | On `main`? |
|----|-------|-------|-----------|
| #1 | PPTX path | merged | ✓ |
| #2 | PDF path | merged (into pptx branch) | ✓ via #5 |
| #3 | FastAPI backend | merged (into pdf branch) | ✓ via #5 |
| #4 | React frontend | merged (into backend branch) | ✓ via #5 |
| #5 | Land stack on `main` | **merged** | ✓ |

The four `feature/*` branches were intentionally **kept** (not deleted) after merging.

---

## Completed
<!-- List tasks or features that are fully done. Add the date when completed. -->

- [x] `ai_specs/overview.md` — project, goals, tech stack (React + FastAPI, OpenAI-compatible LLM, Render/Temple hosting) — 2026-06-13
- [x] `ai_specs/features.md` — Phase 1 (PPTX+PDF remediation, auth, file workspace, checker, best-effort pass, AI alt-text, report), Phase 2 (Word/video/batch/human-review), Phase 3 (Canvas+Panorama integration) — 2026-06-13
- [x] `ai_specs/domain-knowledge.md` — WCAG 2.1/2.2 AA, YuJa Panorama (Temple's vendor) scoring, the checker-passing vs truly-accessible tension, per-check approach — 2026-06-13
- [x] `ai_specs/architecture-planning.md` — `remediator/` engine (per-format rules P1–P13 / D1–D21, shared scorer, dataclasses), per-user storage, API, auth, config.yaml — 2026-06-13
- [x] `ai_specs/llm-integration.md` — alt-text + title prompts, confidence→placeholder fallback, OpenAI-compatible provider, evaluation — 2026-06-13
- [x] `ai_specs/conventions.md` — naming (`_a11y`, groups, P#/D#), one-way engine dependency, testing, LLM rules — 2026-06-13
- [x] `ai_specs/deployment.md` — Render (persistent disk + Tesseract) / Temple, env vars, Azure SSO setup — 2026-06-13
- [x] Repo scaffold — `remediator/`, `backend/`, `frontend/` (placeholder); `config.yaml`, `requirements.txt`, `pyproject.toml` (black/ruff/pytest), `.env.example`, `.gitignore`, README — 2026-06-13
- [x] Engine core — `models.py` (AuditResult/FixResult/ScoreBreakdown/FileReport), `config.py` (YAML loader), `scorer.py` (weighted, severe-cap, placeholder-aware) — 2026-06-13
- [x] PPTX path — `handlers/pptx_handler.py` (alt-text/decorative OOXML helpers), `rules/pptx_rules.py` (P1–P13 audit), `fixers/pptx_fixer.py` + `fixers/ai_fixer.py`, `llm/provider.py` (OpenAI-compatible) + `llm/prompts.py`, `pipeline.py`, `reporter.py` (JSON+HTML) — 2026-06-13
- [x] CLI — `backend/cli.py` (`fix` command), runs engine end-to-end without the web layer — 2026-06-13
- [x] PDF path — `handlers/pdf_handler.py` (pikepdf; title/lang/tag/image/scanned/link helpers, encrypted/malformed handling), `rules/pdf_rules.py` (D1/D2/D3/D8/D9–D11/D12/D16 audit), `fixers/pdf_fixer.py` (D2+D12 auto-fix, rest reported), registered `.pdf` in `pipeline.py` — 2026-06-13
- [x] Tests — scorer, PPTX + PDF rules and fixers/pipeline (25 passing); fixtures built programmatically (reportlab + pikepdf) in `conftest.py` — 2026-06-13
- [x] FastAPI backend (`backend/app/`) — settings, swappable auth (`MockAuthProvider` + `AzureOIDCProvider` stub) with HMAC signed-cookie sessions, `StorageService` (per-user, path-traversal-safe, atomic metadata writes), `JobManager` (threaded background jobs + polling), Pydantic schemas, routes (auth/groups/files/jobs/reports/config), `main.create_app()` factory + CORS, `/health` — 2026-06-13
- [x] Backend tests — auth, workspace, full remediation flow, auth-isolation (a user cannot reach another user's files/jobs); 41 total passing — 2026-06-13
- [x] React frontend (`frontend/`, Vite) — `services/api.js` (cookie auth), `useAuth`/`useJobStatus` hooks, components (SignInForm, TopPanel, FileExplorer, UploadModal, ReportViewer), pages (HomePage, ReportPage), OpenOwls-themed CSS; ESLint + Prettier + Vitest config; 4 tests passing; builds clean — 2026-06-14
- [x] Full Phase 1 stack landed on `main` (PR #5); verified green on `main` — 2026-06-14
- [x] `docs/application-user-guide.html` — end-user guide: run via CLI or web app, read before/after scores, enable AI alt text (matches the OpenOwls getting-started theme) — 2026-06-14
- [x] Bug fixes from first hands-on PPTX testing (Mac) — (1) title fixer no longer crashes on slides with no title placeholder (Blank layout): `ai_fixer.py` located the layout title via `shapes.title`, which `LayoutShapes` lacks — now found by placeholder idx 0, degrading to unfixed instead of raising; (2) `reportlab` added to `requirements.txt` (used by PDF test fixtures, was missing so PDF tests errored on a clean install); (3) uploads now accept **filenames with spaces** (`storage.py` safe-name regex) — traversal chars still blocked. Regression tests added for (1) and (3); 43 tests pass — 2026-07-13

---

## Blocked
<!-- Anything that cannot move forward and why. -->

| Item | Reason | Owner |
|------|--------|-------|
| Real Azure AD / Temple SSO | Needs Temple IT app registration (client id/secret, tenant, redirect URI). Not a hard blocker — dev uses `AUTH_PROVIDER=mock`. | Faculty + Temple IT |

---

## Up Next
<!-- The next 2-3 tasks to tackle in the current phase -->

- [ ] Full-stack browser E2E: run backend + frontend together and click through sign-in → upload → Fix → report (headless browser); add a couple of frontend integration tests for FileExplorer/ReportViewer against a mocked API.
- [ ] PDF OCR (D8): add a text layer to scanned PDFs (Tesseract via pytesseract/pdf2image or ocrmypdf as a subprocess); guard on binary availability and degrade to report-only otherwise.
- [ ] PDF structure (D1/D3/D4/D5/D7): synthesize a logical structure tree and write `/Alt` on figures (evaluate Adobe Auto-Tag API; likely partly Phase 2 per the risk note).
- [ ] Wire real `AzureOIDCProvider` (OAuth2/OIDC redirect + tenant restriction) once Temple IT app registration lands.
- [ ] Validate real PPTX captioning against a live OpenAI-compatible endpoint (set `LLM_*`); spot-check alt-text quality per `llm-integration.md` evaluation targets.

---

## Notes / Decisions
<!-- Key decisions worth remembering. -->

- Phase 1 handles **both PPTX and PDF**; engine is built around pluggable per-format handlers/rules so Word/video are easy to add in Phase 2.
- LLM is behind an **OpenAI-compatible interface** — no vendor SDK hard-coded.
- Report surfaces **two scores**: checker-passing (counts placeholders as passing) vs truly-remediated (excludes them).
- **Highest-risk area:** PDF structural tagging (D1/D4/D7) — pikepdf is low-level; expect many "needs review" results.
- A prior similar planning doc (`accessibility-planning.md`, by another author) informed the engine details (rule tables, scoring, dataclasses); its single-user/no-auth and hard-coded-Anthropic choices were intentionally overridden.

---

## Session Log
<!-- Brief note after each work session. Most recent at the top. -->

- **2026-07-13 (first hands-on PPTX testing + fixes)** — Set up a Mac dev venv at `~/.venvs/accessibility-automator` (the in-repo `.venv/` is the Windows one; repo lives in a shared OneDrive folder used from both OSes) and exercised the PPTX path from the CLI. Testing surfaced and fixed three issues: (1) **crash** in the slide-title fixer on decks whose slides have no title placeholder — `ai_fixer._ensure_title_placeholder` read `slide.slide_layout.shapes.title`, but `LayoutShapes` has no `.title` (only `SlideShapes` does), so it raised `AttributeError` and killed the whole job; now it finds the layout title by placeholder idx 0 and degrades to "not fixed" per the never-crash rule. (2) **`reportlab` missing from `requirements.txt`** though the PDF test fixtures import it — added it (a clean install now runs the full suite). (3) **filenames with spaces** were rejected by the storage safe-name regex — added space to the allowed set (traversal chars `..`/`/`/`\\` still blocked; frontend already URL-encodes names). Verified a demo deck 50→100 (checker)/71 (truly remediated) with valid reopenable output; added regression tests; **43 Python tests pass**, black/ruff clean. Also created local `.env` files and confirmed backend+frontend start (no full browser click-through yet). Committed to `docs/user-guide-and-progress`.
- **2026-06-14 (landing + docs)** — Merged **PR #5** (`feature/react-frontend` → `main`) to bring the full stack onto `main` (the stacked #1–#4 had merged into intermediate branches). Confirmed green on `main`: 41 Python + 4 frontend tests, `vite build` clean. Merged feature branches were intentionally kept. Wrote `docs/application-user-guide.html` — a faculty-facing guide for running the app (CLI + web) and reading the before/after scores. Phase 1 is now fully on `main`; remaining items are the deferrals in Up Next (live-LLM check, deeper PDF, real SSO, browser E2E).
- **2026-06-14 (status review)** — Reviewed where everything stands. All Phase 1 code is written/tested (41 Python + 4 frontend tests passing, linters clean). Discovered the stacked PRs #1–#3 were merged into their intermediate base branches rather than up to `main`, so `main` has the PPTX path only; PDF/backend/frontend live in PR #4's chain. Recommended retargeting #4 to `main` to land the rest in one merge (see Integration / Branch State). No code changes this session.
- **2026-06-14** — Built the React (Vite) frontend on a branch stacked on the backend branch. `services/api.js` talks to the API with `credentials: "include"` (cookie auth); `useAuth` context checks the session on mount; `useJobStatus` polls jobs ~2s. UI: SignInForm (mock login), HomePage with TopPanel (name/email) + FileExplorer (groups/files, before→after→truly-fixed scores, **Fix** button with live progress, download original/remediated, report link), UploadModal (group + PPTX/PDF), and ReportPage/ReportViewer (three scores + genuine/placeholder/manual sections with placeholder Acknowledge → POST signoff). OpenOwls-themed CSS. ESLint/Prettier/Vitest configured; 4 tests pass; `vite build` and `eslint` clean; dev server serves the app and the entry module compiles. Did **not** yet do a headless-browser click-through (added to Up Next).
- **2026-06-13 (impl 3)** — Built the FastAPI backend (branch stacked on the PDF branch). `backend/app/`: env-driven settings; swappable auth (`MockAuthProvider` active, `AzureOIDCProvider` stub) behind HMAC signed-cookie sessions (stdlib, no extra dep); `StorageService` with strict name validation (no `..`/separators), per-user input/output dirs, `_a11y` outputs, and atomic `metadata.json` writes; `JobManager` running remediation on a thread pool with status polling; Pydantic schemas; routes for auth/groups/files(upload+download+signoff)/jobs/reports/config + `/health`; `create_app()` factory with CORS and state on `app.state` for testability. Added 16 API tests incl. auth-isolation (a user can't reach another's files or jobs); 41 total pass; black/ruff clean. Smoke-tested live via uvicorn (login→upload→list over real HTTP). No LLM in tests → deterministic placeholder behavior.
- **2026-06-13 (impl 2)** — Built the PDF path on a branch stacked on the PPTX branch. `pdf_handler.py` (pikepdf) opens files, handles encrypted/corrupted gracefully (copies original through on save), and exposes helpers for title/language/tagging/images/scanned-page/link detection (scanned detection parses the content stream for text operators, since reportlab adds fonts to image-only pages). `pdf_rules.py` audits D1/D2/D3/D8/D9–D11/D12/D16; `pdf_fixer.py` auto-fixes D2+D12 and honestly reports the rest as needs-manual. Registered `.pdf` in the pipeline. Added 9 PDF tests (reportlab/pikepdf fixtures); 25 total pass; black/ruff clean. Also corrected the CLI summary (was counting `not_fixed` as genuine fixes). Verified CLI on a demo PDF: 55 → 82, title+lang written. **Scoped out for now (flagged to sponsor):** real OCR and structure-tree synthesis — they need Tesseract and more than pikepdf provides.
- **2026-06-13 (impl 1)** — Scaffolded the repo and built the full PPTX remediation path. Engine: models, YAML config, weighted scorer (severe-cap + placeholder-aware), PPTX handler with OOXML alt-text/decorative helpers, P1–P13 audit rules, deterministic + AI fixers, OpenAI-compatible LLM provider (httpx, no vendor SDK) with placeholder fallback, pipeline, and JSON/HTML reporter. CLI `fix` runs it end-to-end. 16 tests pass; black/ruff clean. Verified on a demo deck (44 → 100 checker / 75 truly-remediated in placeholder mode) and confirmed the output reopens as valid PPTX. Used Python 3.12 venv (system Python is 3.9; conventions require 3.11+). Added a small heuristic: bare-filename alt text (e.g. python-pptx's default `image.png`) is treated as missing.
- **2026-06-13** — Worked through the full application concept with faculty sponsor and filled in all seven `ai_specs/` files. Researched WCAG + YuJa Panorama to ground `domain-knowledge.md`. Resolved an overview/features conflict around auth/storage. Specs ready for Claude Code implementation.
