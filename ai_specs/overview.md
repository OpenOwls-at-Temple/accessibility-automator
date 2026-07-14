# Overview

> **OpenOwls SDD** — Read by the business sponsor and the full team.
> Describes the project at a high level: what it is, why it exists, who it is for, and what technology it uses.

---

## Project Name
<!-- The name of the application -->

**Accessibility Automator**

## One-Line Description
<!-- Summarize the project in a single sentence -->

_A standalone web app that helps Temple University faculty automatically remediate their lecture materials (PowerPoint and PDF) so they pass WCAG accessibility checks when uploaded to Canvas._

---

## Problem Statement
<!-- What problem does this application solve? Why does it need to exist? -->

Temple faculty upload lecture materials (mainly PowerPoint and PDF) to Canvas, where a third-party tool (e.g. YuJa Panorama or Anthology Ally) scores each file against the WCAG standard, displays a score out of 100, flags the specific accessibility issues, and provides an interactive panel to fix them one at a time. After each manual fix the tool re-runs and updates the score.

Doing this by hand — writing alt text for every image, setting slide titles, fixing color contrast, correcting reading order, adding table headers, repairing link text — is slow, repetitive, and requires accessibility expertise that most faculty don't have the time to build. As a result, many materials remain non-compliant.

Accessibility Automator removes the manual loop: a faculty member uploads a file, the app automatically remediates the accessibility issues, and the file comes back ready to score at or near 100 when re-uploaded to Canvas — along with a report of exactly what was changed.

---

## Goals
<!-- What does success look like for this project? List 3-5 measurable goals. -->

- Automatically remediate uploaded **PPTX and PDF** files so they pass the WCAG checks Canvas's vendor enforces (target: a near-100 score on re-upload).
- Cut the time to remediate a typical lecture file from tens of minutes of manual work to a few minutes of automated processing.
- Use a vision-capable LLM to generate best-effort **alt text and slide titles** for images and untitled content.
- When an issue cannot be confidently fixed, still make it **pass the checker** (placeholder value, or marking purely decorative images as decorative) rather than leaving it as a failure.
- Produce a **detailed before/after report** that clearly separates genuinely-fixed items from placeholder items that still need human follow-up.

## Non-Goals
<!-- What is explicitly out of scope? This is as important as the goals. -->

- No direct Canvas or vendor (Panorama / Ally) API integration in Phase 1 — that is planned for Phase 3.
- No Word or video support in Phase 1 — that is planned for Phase 2 (the architecture must make adding formats easy).
- Not a legal guarantee of full accessibility or WCAG conformance. "Checker-passing" is not the same as "perfectly accessible," and the app must be honest about that distinction.
- Does not remediate the Canvas course shell itself — only the uploaded documents.
- Sign-in is **Google SSO + an admin-managed invite allowlist** (no self-service sign-up). Because a plain Temple email domain check cannot distinguish faculty from students, access is granted per-account by an admin; this bounds the user base and the attack surface. A local-only dev login supports development before Google credentials exist.
- Beyond the single **admin** role (who can invite/deactivate users), there are no fine-grained role-based permissions, admin analytics dashboards, or sharing between users in Phase 1.

---

## Target Users
<!-- Who will use this application? Describe each type of user briefly. -->

| User Type | Description |
|-----------|-------------|
| Primary User | Temple faculty / instructors preparing lecture materials for upload to Canvas |
| Secondary User | Instructional designers and accessibility reviewers who support faculty |
| Indirect Beneficiary | Students using assistive technology who consume the materials |

---

## Tech Stack
<!-- What technologies will be used? Be specific about versions where it matters. -->

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 18 (Vite) | Upload → view report → download flow; matches the team's other apps |
| Backend | FastAPI (Python 3.11+), managed with **uv** | Best ecosystem for document remediation; REST API consumed by the React frontend |
| Document Processing | python-pptx (PPTX), pikepdf / reportlab / OCR tooling (PDF) | Read, edit, and re-tag documents programmatically |
| AI / LLM | Vision-capable model behind an **OpenAI-compatible interface** | Provider is swappable (e.g. OpenAI GPT-4o, Anthropic Claude via a compatible gateway, or a self-hosted model). Used for alt-text and title captioning. |
| Auth | **Google SSO (Google Identity Services)** + an **admin-managed invite allowlist**; JWT bearer sessions (authlib). A local-only dev login is available. | Sign-in restricted to a configured Temple email domain AND to accounts an admin has added — no self-service sign-up. |
| Storage | Server filesystem for documents (per-user folders keyed by email username) **+ a small SQL database for the user allowlist only** | Files: `input/<group>/...`, `output/<group>/...`. DB: **SQLite on the persistent disk** in both local and prod (users table only — SQLAlchemy + Alembic); Supabase Postgres is a supported alternative. |
| Hosting | Render (low-cost tier) — or the Temple data center if access and approval are obtained | Final choice depends on Temple IT approval timelines |

---

## Stakeholders
<!-- Who is involved in this project and in what capacity? -->

| Name / Role | Responsibility |
|-------------|----------------|
| Faculty Sponsor (Alex Pang) | Defines scope, reviews milestones, owns `overview.md` and Phase 1 of `features.md` |
| Student Team | Design, implementation, deployment; own architecture, conventions, and deployment specs |
| End Users (faculty testers) | Testing and feedback on real lecture materials |

---

## Key Constraints
<!-- Any important limitations — time, budget, technical, compliance, etc. -->

- Must be completable within one semester by a student team.
- Cost is a serious consideration, but it should **not artificially limit the design** — choose the right tools and models, and keep an eye on LLM API spend rather than capping it prematurely.
- The LLM must sit behind an **OpenAI-compatible interface** so the underlying model/provider can be swapped without changing application code.
- Must not store student data; the app handles only faculty-uploaded course materials and should be FERPA-aware.
- Output files must remain valid and openable in PowerPoint / Acrobat and be re-uploadable to Canvas without errors.
- The app must be transparent about the difference between **checker-passing** and **genuinely accessible**, surfacing placeholder fixes that need human review.
