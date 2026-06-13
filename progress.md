# Progress

> **OpenOwls SDD** — Living status document. Update this file at the end of every work session.
> Claude Code reads this first at the start of every new session to catch up on project state.

## Current Phase
<!-- Which phase are we actively working on? e.g. Phase 1 -->

**Active Phase:** Phase 1 — implementation underway. Repo scaffolded; PPTX path complete; PDF path (metadata fixes + structural detection) complete.

## Status Summary
<!-- One or two sentences describing where the project stands right now -->

The `remediator/` engine audits, fixes, re-scores, and reports on **both PPTX (P1–P13) and PDF** files end-to-end, via library or `python -m backend.cli fix`. PDF Phase 1 reliably auto-fixes metadata (D2 title, D12 language) and **detects** the structural checks (D1 untagged, D3 image alt, D8 scanned, D9–D11 integrity, D16 links), reporting them honestly as "needs manual fix" rather than faking them — matching the architecture risk note. 25 tests pass; `black`/`ruff` clean. **Deferred to dedicated follow-ups:** PDF OCR text-layer insertion (D8) and structure-tree synthesis / alt-text writing (D1/D3), both of which need system binaries (Tesseract) and more than pikepdf can do alone. Next after that: the FastAPI app, then the React UI.

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

---

## In Progress
<!-- What is actively being worked on right now? -->

- [ ] _(none — PPTX + PDF paths landed)_

---

## Blocked
<!-- Anything that cannot move forward and why. -->

| Item | Reason | Owner |
|------|--------|-------|
| Real Azure AD / Temple SSO | Needs Temple IT app registration (client id/secret, tenant, redirect URI). Not a hard blocker — dev uses `AUTH_PROVIDER=mock`. | Faculty + Temple IT |

---

## Up Next
<!-- The next 2-3 tasks to tackle in the current phase -->

- [ ] PDF OCR (D8): add a text layer to scanned PDFs (Tesseract via pytesseract/pdf2image or ocrmypdf as a subprocess); guard on binary availability and degrade to report-only otherwise.
- [ ] PDF structure (D1/D3/D4/D5/D7): synthesize a logical structure tree and write `/Alt` on figures (evaluate Adobe Auto-Tag API; likely partly Phase 2 per the risk note).
- [ ] FastAPI layer (`backend/app/`): mock auth first, per-user storage service, job runner, routes (groups/files/jobs/reports/signoff), then `AzureOIDCProvider`.
- [ ] React UI (`frontend/`): sign-in, file explorer, upload, status polling, report viewer, sign-off modal.
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

- **2026-06-13 (impl 2)** — Built the PDF path on a branch stacked on the PPTX branch. `pdf_handler.py` (pikepdf) opens files, handles encrypted/corrupted gracefully (copies original through on save), and exposes helpers for title/language/tagging/images/scanned-page/link detection (scanned detection parses the content stream for text operators, since reportlab adds fonts to image-only pages). `pdf_rules.py` audits D1/D2/D3/D8/D9–D11/D12/D16; `pdf_fixer.py` auto-fixes D2+D12 and honestly reports the rest as needs-manual. Registered `.pdf` in the pipeline. Added 9 PDF tests (reportlab/pikepdf fixtures); 25 total pass; black/ruff clean. Also corrected the CLI summary (was counting `not_fixed` as genuine fixes). Verified CLI on a demo PDF: 55 → 82, title+lang written. **Scoped out for now (flagged to sponsor):** real OCR and structure-tree synthesis — they need Tesseract and more than pikepdf provides.
- **2026-06-13 (impl 1)** — Scaffolded the repo and built the full PPTX remediation path. Engine: models, YAML config, weighted scorer (severe-cap + placeholder-aware), PPTX handler with OOXML alt-text/decorative helpers, P1–P13 audit rules, deterministic + AI fixers, OpenAI-compatible LLM provider (httpx, no vendor SDK) with placeholder fallback, pipeline, and JSON/HTML reporter. CLI `fix` runs it end-to-end. 16 tests pass; black/ruff clean. Verified on a demo deck (44 → 100 checker / 75 truly-remediated in placeholder mode) and confirmed the output reopens as valid PPTX. Used Python 3.12 venv (system Python is 3.9; conventions require 3.11+). Added a small heuristic: bare-filename alt text (e.g. python-pptx's default `image.png`) is treated as missing.
- **2026-06-13** — Worked through the full application concept with faculty sponsor and filled in all seven `ai_specs/` files. Researched WCAG + YuJa Panorama to ground `domain-knowledge.md`. Resolved an overview/features conflict around auth/storage. Specs ready for Claude Code implementation.
