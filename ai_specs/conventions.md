# Conventions

> **OpenOwls SDD** — Read by engineers and the AI coding assistant.
> Defines how code is written on this project. These rules apply to every file, every session.
> Claude Code must follow these conventions without being reminded each time.

---

## Language & Framework Versions
<!-- Be specific. This prevents the AI from using deprecated syntax. -->

| Technology | Version |
|------------|---------|
| Python | 3.11+ |
| Package manager (Python) | **uv** (`pyproject.toml` + `uv.lock`; no `requirements.txt`) |
| Node.js | 20+ |
| React | 18+ |
| Vite | 5+ |
| FastAPI | 0.111+ |
| SQLAlchemy | 2+ (with Alembic for migrations) |
| Authlib | 1.3+ (JWT) |
| python-pptx | 0.6.23+ |
| pikepdf | 8+ |
| pytesseract | 0.3.10+ (requires Tesseract installed on the OS) |
| Pydantic | 2+ |

---

## Naming Conventions

| Context | Convention | Example |
|---------|------------|---------|
| Python variables & functions | `snake_case` | `audit_pptx_file()` |
| Python classes | `PascalCase` | `PptxHandler`, `LLMProvider` |
| React components | `PascalCase` | `FileExplorer.jsx` |
| React hooks | `camelCase` prefixed with `use` | `useJobStatus` |
| CSS classes | `kebab-case` | `file-explorer-row` |
| Environment variables | `UPPER_SNAKE_CASE` | `LLM_API_KEY` |
| Git branches | `type/short-description` | `feature/pptx-alt-text` |
| **Remediated output files** | `<name>_a11y.<ext>` | `lecture1.pptx → lecture1_a11y.pptx` |
| **Groups (folders)** | the course code as entered by the user | `CIS4526` |
| **Audit check IDs** | `P#` for PPTX, `D#` for PDF | `P3`, `D8` |

---

## File & Folder Conventions

- One React component per file; the file name matches the component name exactly.
- API route files are named after the resource they handle (`groups.py`, `jobs.py`, `auth.py`).
- All LLM prompts live in `remediator/llm/prompts.py` — never inline.
- Tests mirror the source layout: `backend/tests/`, `remediator/tests/`, fixtures in `remediator/tests/fixtures/`.
- **The engine (`remediator/`) must never import from `backend/`.** The dependency is strictly one-way (web layer → engine). This keeps the engine usable via the CLI and ready for the Phase 3 Canvas connector.

---

## Domain-specific code rules

- **Never modify or delete a user's original input file.** Every fix produces a new `_a11y` file in `output/<group>/`.
- A remediation job must **always finish and produce a valid output file**, even if every LLM call fails — failures degrade to placeholders, never crashes.
- Keep **checker-passing** and **truly-remediated** scores distinct; never report a placeholder as a genuine fix.
- Each user can only access their own workspace; resolve the workspace path from the authenticated user, never from a client-supplied path.

## Package management (Python)

- Use **uv**. Add/remove dependencies in `pyproject.toml` (runtime under `[project.dependencies]`, tooling under `[dependency-groups] dev`) and commit the updated **`uv.lock`**. There is **no `requirements.txt`**.
- Run things with `uv run …` (e.g. `uv run pytest`, `uv run uvicorn backend.app.main:app`). On a manually-managed venv (e.g. the Mac `~/.venvs/...`), activate it and skip the `uv run` prefix.
- Never `pip install` into the project ad hoc — add the dep to `pyproject.toml` and re-lock.

## Auth conventions

- Sign-in is **Google SSO + an admin-managed allowlist**; the backend **never auto-provisions** a user. Google verifies identity, the `users` table authorizes.
- Sessions are **JWT bearer** tokens (authlib, HS256), signed with `JWT_SECRET`; the frontend sends `Authorization: Bearer`. Because a bearer token can't ride a plain `<a href>`, authed file downloads go through a fetch-then-blob helper.
- `/auth/dev-login` must stay **local-only** (404 when `ENVIRONMENT != local`) and still require a registered, active user.
- DB schema changes go through an **Alembic migration** (never `create_all` in app startup); keep migrations additive/backward-compatible.

---

## Code Style

- **Python:** PEP 8, formatted with `black`; lint with `ruff`.
- **JavaScript/React:** ESLint recommended rules; format with `prettier`.
- Maximum line length: 100 characters.
- No commented-out code in commits — delete it, or leave a `TODO:` with explanation.
- No `console.log` / stray `print` debugging left in committed code (use the logger).

---

## Git Conventions

- Commit messages: `type: short description` — types `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. Example: `feat: add P3 alt-text fixer`.
- Every feature on its own branch; no direct commits to `main`.
- Pull requests require at least one review before merging.

---

## Testing Conventions

- **Every audit rule** has at least one known-bad and one known-good fixture; tests assert the `AuditResult`.
- **Every fixer** has a test that applies the fix, re-audits, and asserts the issue is resolved (or correctly placeholdered).
- An **auth-isolation** test asserts a user cannot reach another user's files.
- Tests must pass before any PR is merged.
- Test naming: `test_[module].py` (Python), `[module].test.js` (JS). Use descriptive names, e.g. `test_user_cannot_access_other_user_workspace`.

---

## LLM / AI Conventions

- All prompts are defined in `remediator/llm/prompts.py`; never hardcode prompts in fixers or routes.
- LLM access goes through the **OpenAI-compatible `LLMProvider`** — do not import a specific vendor SDK directly.
- Every LLM call has error handling and a **placeholder fallback** (timeout, malformed JSON, rate limit, low confidence).
- LLM calls are **server-side only**; the frontend never calls the LLM.
- Do **not** send PII or any student data to the LLM — only faculty course-material content.

---

## What Claude Code Should Never Do

- Never modify files in `ai_specs/` without explicit instruction.
- Never modify or overwrite a user's original input file.
- Never let `remediator/` import from `backend/`.
- Never skip writing tests to save time.
- Never hardcode a specific LLM vendor SDK or model — use the configurable provider.
- Never add a library without declaring it in `pyproject.toml` (+ `uv.lock`) / `package.json` — and ask first.
- Never auto-provision a user on sign-in, and never leave `/auth/dev-login` enabled outside `local`.
- Never expose secrets or environment variables in frontend code.
