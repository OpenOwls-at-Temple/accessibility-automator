# CLAUDE.md
> This project follows the **OpenOwls SDD (Spec-Driven Development) Process**.
> Read the files below in order before doing any work.

## Session Startup — Read These First

1. **`progress.md`** (project root) — catch up on what has been done, what is in progress, and what is blocked
2. **`ai_specs/overview.md`** — understand the project goals, stakeholders, and tech stack
3. **`ai_specs/features.md`** — understand the full feature scope and which phase we are currently in
4. **`ai_specs/architecture-planning.md`** — understand folder structure, design decisions, and implementation details
5. **`ai_specs/domain-knowledge.md`** — understand domain-specific concepts and constraints
6. **`ai_specs/conventions.md`** — follow all coding conventions, naming rules, and workflow standards without exception
7. **`ai_specs/deployment.md`** — understand hosting platforms, environment variables, and deployment process
8. **`ai_specs/llm-integration.md`** — understand the LLM's role, prompt design, architecture, and evaluation criteria

## Current State (as of 2026-07-01)

**Active Phase: 2** — Phase 1 is complete and on `main`. Phase 2 F11 + F12 are built on branch `fix/test-suite-issues` (not yet merged).

### What is built and working
- Full PPTX + PDF remediation pipeline (`remediator/`) — audit → fix → re-score → report
- FastAPI backend with mock auth, per-user storage, background jobs, REST API
- React frontend — sign in, upload, Fix All, per-file progress, report viewer, placeholder sign-off
- **F11**: Fix All button shows live per-file progress (which file is being processed, X of Y)
- **F12**: Review AI modal — scan a file for AI suggestions, edit them, apply approved text to output file
- **Anthropic provider** — `AnthropicProvider` in `remediator/llm/provider.py` auto-selected when `LLM_BASE_URL` contains `anthropic.com`. Ready for Fable 5.
- 41 Python tests passing, frontend builds clean

### To connect Fable 5 — just set these 3 lines in `.env`
```
LLM_API_KEY=sk-ant-...
LLM_BASE_URL=https://api.anthropic.com
LLM_MODEL=claude-fable-5
```
No code changes needed. The provider auto-detects from the URL.

### How to run locally
```bash
# Backend
cd accessibility-automator
.venv/bin/uvicorn backend.app.main:app --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev
```
Then open http://localhost:5173. Sign in with any email (mock auth). Upload a PPTX or PDF.

### Branch state
- `main` — Phase 1 complete
- `fix/test-suite-issues` — Phase 1 bug fixes + Phase 2 F11/F12 + Anthropic provider (needs PR + merge)

## General Instructions

- Always work within the current phase defined in `ai_specs/features.md`. Do not implement features from a future phase unless explicitly instructed.
- After completing any meaningful unit of work, update `progress.md` to reflect what was done.
- If you encounter a conflict between these spec files, flag it to the user before proceeding.
- If a spec file is missing a detail you need, ask the user rather than assuming.
- Never delete or overwrite any file in `ai_specs/` without explicit instruction.
