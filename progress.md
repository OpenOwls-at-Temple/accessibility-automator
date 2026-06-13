# Progress

> **OpenOwls SDD** — Living status document. Update this file at the end of every work session.
> Claude Code reads this first at the start of every new session to catch up on project state.

## Current Phase
<!-- Which phase are we actively working on? e.g. Phase 1 -->

**Active Phase:** Phase 1 — specs complete, implementation not yet started.

## Status Summary
<!-- One or two sentences describing where the project stands right now -->

All `ai_specs/` files are filled in for **Accessibility Automator**: a standalone web app (React + FastAPI) that remediates faculty PPTX/PDF lecture files against WCAG so they score near-100 in Canvas/YuJa Panorama. The specs are ready to hand to Claude Code for implementation, starting with the `remediator/` engine.

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

---

## In Progress
<!-- What is actively being worked on right now? -->

- [ ] _(none — ready to begin implementation)_

---

## Blocked
<!-- Anything that cannot move forward and why. -->

| Item | Reason | Owner |
|------|--------|-------|
| Real Azure AD / Temple SSO | Needs Temple IT app registration (client id/secret, tenant, redirect URI). Not a hard blocker — dev uses `AUTH_PROVIDER=mock`. | Faculty + Temple IT |

---

## Up Next
<!-- The next 2-3 tasks to tackle in the current phase -->

- [ ] Scaffold the repo per `architecture-planning.md` (frontend/, backend/, remediator/).
- [ ] Implement the engine PPTX path first: `models.py` + `scorer.py` → `rules/pptx_rules.py` (P1–P13) → `fixers/pptx_fixer.py` + `llm/provider.py` + `ai_fixer.py` → `reporter.py`, runnable via `backend/cli.py`.
- [ ] Then PDF path (`pdf_rules.py`, `pdf_fixer.py` incl. OCR), then the FastAPI layer (mock auth first), then the React UI.

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

- **2026-06-13** — Worked through the full application concept with faculty sponsor and filled in all seven `ai_specs/` files. Researched WCAG + YuJa Panorama to ground `domain-knowledge.md`. Resolved an overview/features conflict around auth/storage. Specs ready for Claude Code implementation.
