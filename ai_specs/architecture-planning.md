# Architecture Planning

> **OpenOwls SDD** — Read by the system architect and software engineers.
> Defines the folder structure, key design decisions, and implementation details.
> Claude Code uses this file to understand how the codebase is organized.

---

## System Architecture Overview
<!-- Describe the high-level architecture. How do the main components interact? -->

Accessibility Automator is a three-tier web application:

- **Frontend** — React 18 (Vite) single-page app. Handles sign-in, the file-explorer home page, uploads, the "Fix" action, progress display, and the remediation report.
- **Backend** — FastAPI (Python 3.11+) REST API. Handles authentication, per-user file storage, and orchestrating remediation jobs. The LLM is called **server-side only**.
- **Remediation engine** — a standalone Python package (`remediator/`) that does the actual audit → fix → re-score → report work. It is **decoupled from the web layer**: it can be imported by the backend *and* run directly as a CLI. The engine **never imports from the backend** — the dependency is strictly one-way.

There is **no relational database in Phase 1**. State lives on the server filesystem: each user gets a private workspace folder, and each remediation writes a JSON report next to its output file.

Flow: user signs in (Temple SSO, or a dev mock) → uploads files into a **group** (usually a course code) → clicks **Fix** → backend starts a **background job** that processes files one at a time → frontend **polls a status endpoint** → when done, the user sees before/after scores and a report, and downloads the remediated `_a11y` files.

---

## Folder Structure
<!-- Show the intended folder structure. Add a comment explaining each key folder. -->

```
project-root/
├── CLAUDE.md
├── progress.md
├── ai_specs/
├── config.yaml                  # Central runtime configuration (see §Configuration)
├── frontend/                    # React + Vite SPA
│   ├── src/
│   │   ├── components/          # FileExplorer, UploadModal, ReportViewer, SignOffModal, ...
│   │   ├── pages/               # HomePage, GroupPage, ReportPage
│   │   ├── hooks/               # e.g. useAuth, useJobStatus (polling)
│   │   ├── services/            # API client functions
│   │   └── utils/
│   ├── tests/
│   └── public/
├── backend/                     # FastAPI web layer (MAY import remediator/)
│   ├── app/
│   │   ├── routes/              # auth, groups, files, jobs, reports, config
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # storage service, job runner
│   │   └── auth/                # auth interface + providers (mock, azure_oidc)
│   ├── cli.py                   # Thin CLI entry (delegates to remediator/)
│   └── tests/
└── remediator/                  # The engine — MUST NOT import from backend/
    ├── pipeline.py              # audit → fix → re-score → report orchestration
    ├── models.py                # AuditResult, FixResult, FileReport dataclasses
    ├── scorer.py                # weighted scoring model
    ├── reporter.py              # JSON + HTML report generation
    ├── handlers/
    │   ├── base.py              # FormatHandler interface (open/read/write a file)
    │   ├── pptx_handler.py
    │   └── pdf_handler.py
    ├── rules/
    │   ├── pptx_rules.py        # P1–P13 audit checks
    │   └── pdf_rules.py         # D1–D21 audit checks
    ├── fixers/
    │   ├── pptx_fixer.py        # deterministic PPTX fixes
    │   ├── pdf_fixer.py         # deterministic PDF fixes (incl. OCR)
    │   └── ai_fixer.py          # alt text + titles via the LLM provider
    ├── llm/
    │   ├── provider.py          # OpenAI-compatible client (swappable)
    │   └── prompts.py
    └── tests/
        └── fixtures/            # one known-bad + one known-good file per rule
```

### Per-user storage layout (on disk)

```
<STORAGE_DIR>/users/<email_username>/
├── input/
│   └── <group>/                 # group = course code, e.g. CIS4526
│       └── lecture1.pptx        # original — NEVER modified or deleted
├── output/
│   └── <group>/
│       ├── lecture1_a11y.pptx   # remediated output (_a11y suffix)
│       └── lecture1_a11y.report.json
└── metadata.json                # groups, files, scores, signoffs (audit trail)
```

---

## Key Design Decisions
<!-- Document important architectural choices and the reasoning behind them. -->

| Decision | Choice | Reason |
|----------|--------|--------|
| API style | REST (`/api/v1`) | Simple for students to learn and debug |
| Engine isolation | `remediator/` is import-only, one-way dependency, also runnable as CLI | Testable in isolation; reusable; lets a Canvas connector slot in for Phase 3 without touching the engine |
| Rule organization | **Per-format** rule modules sharing common dataclasses + one scorer | PPTX and PDF checks genuinely differ (13 vs 21); per-format is simpler and more honest than forcing a single format-agnostic rule set |
| Processing model | **Background job + status polling** (every ~2s) | LLM captioning is slow on big decks; keeps the UI responsive |
| Auth | Pluggable `AuthProvider` interface: `MockAuthProvider` (dev) + `AzureOIDCProvider` (prod) | Decouples build from Temple IT approval; restrict to Temple accounts in prod |
| LLM access | Vision model behind an **OpenAI-compatible** `LLMProvider`, server-side only | Provider/model swappable; API key stays on server |
| Storage | Server filesystem, per-user folders; metadata in JSON | No DB needed in Phase 1; per-user isolation by design |
| Output naming | `<name>_a11y.<ext>` in `output/<group>/`; originals untouched | Clear, non-destructive convention |
| Scoring | Weighted average by severity, with a Severe-issue score cap | Approximates Panorama's weighted model (see Domain Knowledge) |
| Honesty | Report two numbers: **checker-passing score** and **truly-remediated estimate** (excludes placeholders) | Keeps the tool honest about "passes the checker" vs "actually accessible" |

---

## The Remediation Engine

Each file type has a **handler** (opens the file, exposes its content, writes changes back), a **rules module** (audit checks producing `AuditResult`s), and a **fixer** (applies deterministic + AI fixes producing `FixResult`s). The **scorer** and **reporter** are shared across formats. The **pipeline** ties it together:

1. **Audit** the input → list of `AuditResult` → **pre-fix score**.
2. **Fix** each violation (deterministic fix, AI fix, placeholder, or report-only) → list of `FixResult`.
3. **Re-audit** the output → **post-fix score** (checker-passing) and a **truly-remediated score** that does not count placeholders.
4. **Report** → `pre_fix.json`, `post_fix.json`, and an HTML report.

### Panorama rule sets

These approximate the YuJa Panorama checklist (WCAG 2.1/2.2 AA basis). Severity feeds the scorer; the strategy column says how Phase 1 handles each.

**PPTX — P1–P13**

| # | Issue | Severity | Strategy |
|---|-------|----------|----------|
| P1 | Document missing title (metadata) | Major | Auto: set `core_properties.title` |
| P2 | Slide has no title | Major | AI suggests title; placeholder `"Slide {N}"` if AI off/low-confidence |
| P3 | Image/object has no alt text | Major | AI vision caption; placeholder if low-confidence; mark decorative if applicable |
| P4 | Insufficient color contrast | Major | Report-only with exact ratio + hex recommendation (don't silently alter branding) |
| P5 | Table has no header row | Major | Auto: mark first row as header (verify Panorama credits this) |
| P6 | Language not specified | Minor | Auto: set language (`en-US`, configurable) |
| P7 | Incorrect language set | Minor | Auto: correct language |
| P8 | Hyperlink text not descriptive | Minor | Report-only with URL + surrounding text |
| P9 | Font size < 9pt | Minor | Report-only (design decision) |
| P10 | Reading order not set | Minor | Auto: reset tab order top-to-bottom, left-to-right by position |
| P11 | Document malformed | Severe | Report-only; score capped |
| P12 | Document encrypted | Severe | Report-only; score capped |
| P13 | Outdated format (.ppt) | Disabled | Auto: convert to .pptx (note formatting may shift) |

**PDF — D1–D21** (highlights; full set implemented in `pdf_rules.py`)

| # | Issue | Severity | Strategy |
|---|-------|----------|----------|
| D1 | PDF untagged | Major | Auto: add tag structure (⚠ hardest area — often partial, flag for review) |
| D2 | Document missing title | Major | Auto: set `/Title` (Info dict + XMP) |
| D3 | Image has no alt text | Major | AI vision → `/Alt` on Figure tag; placeholder if low-confidence |
| D4 | No headings at all | Major | Report-only with section recommendations |
| D5 | Headings don't start at H1 | Major | Auto: renumber to start at H1 |
| D6 | Insufficient contrast | Major | Report-only with hex recommendation |
| D7 | Table has no header | Major | Report-only (structural remediation needed) |
| D8 | Scanned (image-only) PDF | Severe | Auto: OCR (pytesseract) → text layer; mark "OCR applied — verify" |
| D9–D11 | Malformed / encrypted / corrupted | Severe | Report-only; score capped |
| D12 | Language not specified | Minor | Auto: set `/Lang` in catalog |
| D13 | Headings not properly nested | Minor | Auto: rebuild hierarchy |
| D14 | Heading depth > 6 | Minor | Report-only |
| D15 | Reading order | Minor | Auto: sort by bounding-box position |
| D16 | Hyperlink text not descriptive | Minor | Report-only |
| D17–D20 | Font<9pt / table summary / list structure / link no URL | Disabled | Not scored in Phase 1 |
| D21 | Scanned → resolved by OCR | Severe→resolved | See D8 |

> **Risk note:** D1/D4/D7 (true PDF structural tagging) are the highest-risk items — `pikepdf` is low-level and cannot easily synthesize a full logical structure tree. Expect many "needs review" results for complex PDFs; consider Adobe Auto-Tag API or deferring the hardest cases to Phase 2.

### Scoring model

```
score = round((weighted_passes / total_weight) × 100)
severity_weight = { Severe: 3, Major: 2, Minor: 1, Disabled: 0 }
total_weight    = sum of weights for all enabled checks for this file type
weighted_passes = sum of weights for checks with no violation
Special rule: if any Severe violation remains after fixing, cap score at 20.
```

The **post-fix checker-passing score** counts placeholdered checks as passing. The **truly-remediated score** counts them as failing — the gap between the two is exactly the human follow-up backlog.

### Placeholder / sign-off mechanism

When `signoff.add_placeholder_for_unfixable: true`, presence-only checks (slide title, alt text) get a configurable placeholder so the mechanical check passes. Content-quality checks (contrast, font size, hyperlink text, PDF table headers) **cannot** be placeholdered and are reported as "Requires manual fix" with specific recommendations. Every placeholder is recorded in the user's `metadata.json` under `signoffs[]` with file, check id, element reference, timestamp, and status (`placeholder` | `acknowledged` | `resolved`). The frontend `SignOffModal` lets users acknowledge items (updates metadata only, no file change).

---

## Data Models
<!-- Describe the main data entities and their key fields. -->

### `AuditResult` / `FixResult` (engine dataclasses)

```python
@dataclass
class AuditResult:
    check_id: str        # "P3"
    severity: str        # "Severe" | "Major" | "Minor" | "Disabled"
    passed: bool
    element_ref: str     # "Slide 4 / Picture 7" or "Page 2 / Image 1"
    detail: str
    recommendation: str

@dataclass
class FixResult:
    check_id: str
    action: str          # "auto_fixed" | "ai_fixed" | "placeholder" | "not_fixed"
    element_ref: str
    detail: str
    success: bool
```

### User metadata (`users/<email_username>/metadata.json`)

```json
{
  "user": "apang",
  "groups": [{
    "name": "CIS4526",
    "files": [{
      "name": "lecture1.pptx",
      "file_type": "pptx",
      "input_path": "input/CIS4526/lecture1.pptx",
      "output_path": "output/CIS4526/lecture1_a11y.pptx",
      "pre_fix_score": 62,
      "post_fix_score": 100,
      "truly_remediated_score": 88,
      "status": "complete"
    }]
  }],
  "signoffs": [{
    "group": "CIS4526", "file": "lecture1.pptx", "check_id": "P3",
    "element_ref": "Slide 4 / Picture 7",
    "placeholder_used": "[Image — description pending instructor review]",
    "status": "placeholder", "acknowledged_at": null, "note": null
  }]
}
```

---

## API Endpoints
<!-- All endpoints require an authenticated Temple user; each user sees only their own workspace. -->

Base path: `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/me` | Current user (name, email, username) |
| GET | `/auth/login` · `/auth/sso/callback` | Sign in (mock in dev, Azure OIDC in prod) |
| POST | `/auth/logout` | Sign out |
| GET | `/groups` | List the user's groups with summary scores |
| GET | `/groups/{group}` | List files in a group (input + output) |
| POST | `/groups/{group}/files` | Upload one or more files into a group (multipart; PPTX/PDF only) |
| POST | `/groups/{group}/remediate` | Start remediation for the group (or selected files) → `{ job_id }` |
| GET | `/jobs/{job_id}` | Poll job status: `{ status, progress, files_done, files_total }` |
| GET | `/groups/{group}/report` · `/report/html` | Group report (JSON / rendered HTML) |
| GET | `/groups/{group}/files/{name}/report` | Per-file report (JSON) |
| POST | `/groups/{group}/files/{name}/signoff` | Acknowledge a placeholder: `{ check_id, action, note }` |
| GET | `/groups/{group}/files/{name}/download?kind=input\|output` | Download original or remediated file |
| GET | `/config` | Effective config (read-only) |

---

## Authentication

`AuthProvider` interface with two implementations selected by `AUTH_PROVIDER`:

- **`MockAuthProvider`** (dev) — enter an email, get the matching workspace. No external dependency.
- **`AzureOIDCProvider`** (prod) — OAuth2 / OIDC against Microsoft Azure AD, redirecting to the Temple login. Restricts sign-in to the Temple tenant. Requires an app registration, redirect URI, client id/secret, and tenant id from Temple IT (early Phase 1 task, gated on IT approval — not a hard blocker).

A successful sign-in establishes a session (signed cookie or JWT). Middleware resolves the current user → their workspace path; users can never access another user's folder.

---

## LLM Integration
<!-- Summary only — full detail lives in ai_specs/llm-integration.md -->

- **Provider:** vision-capable model behind an **OpenAI-compatible** `LLMProvider` (configurable base URL + model). No vendor SDK is hard-coded.
- **Called from:** `remediator/fixers/ai_fixer.py`, server-side only.
- **Input:** image bytes (for alt text) or slide/section text (for titles).
- **Output:** a short description/title **plus a confidence signal**; low confidence → treat as placeholder.
- **Prompts:** `remediator/llm/prompts.py`.

---

## Environment Variables
<!-- Never put actual values here. -->

| Variable | Description |
|----------|-------------|
| `LLM_API_KEY` | API key for the OpenAI-compatible LLM endpoint |
| `LLM_BASE_URL` | Base URL of the LLM endpoint (lets us swap providers) |
| `LLM_MODEL` | Model name to use (vision-capable) |
| `AUTH_PROVIDER` | `mock` or `azure` |
| `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_TENANT_ID` / `AZURE_REDIRECT_URI` | Azure AD / Temple SSO config (prod only) |
| `SESSION_SECRET` | Secret for signing the session cookie / JWT |
| `STORAGE_DIR` | Root directory for per-user workspaces |
| `CORS_ORIGINS` | Allowed frontend origins |

---

## Configuration

A central `config.yaml` controls non-secret runtime behavior (secrets stay in env vars):

```yaml
llm:
  enabled: true
  generate_alt_text: true
  suggest_titles: true
  max_image_size_kb: 1024        # resize before sending to the API
  confidence_threshold: 0.6      # below this → placeholder

fixes:
  auto_fix_minor: true
  auto_fix_major: true
  convert_old_format: true       # .ppt → .pptx

signoff:
  add_placeholder_for_unfixable: true
  placeholder_alt_text: "[Image — description pending instructor review]"
  placeholder_slide_title_prefix: "Slide"
  default_language: "en-US"

scoring:
  severe_weight: 3
  major_weight: 2
  minor_weight: 1
  severe_cap: 20

storage:
  max_file_size_mb: 50

server:
  cors_origins: ["http://localhost:5173"]
```

---

## Testing Strategy

- **Per-rule unit tests:** one known-bad and one known-good fixture per check; assert the `AuditResult`.
- **Per-fixer tests:** apply the fix, re-audit, assert the issue is resolved (or correctly placeholdered).
- **Integration test:** full pipeline on a sample PPTX and PDF with known issues; assert pre/post scores.
- **API tests:** pytest + httpx async client, including auth isolation (a user cannot reach another user's files).
- Fixtures live in `remediator/tests/fixtures/`.

---

## Implementation Order (suggested)

1. `remediator/models.py`, `scorer.py` — dataclasses + weighted scoring.
2. `remediator/rules/pptx_rules.py` + `handlers/pptx_handler.py` — audit P1–P13.
3. `remediator/fixers/pptx_fixer.py` + `llm/provider.py` + `ai_fixer.py` — PPTX fixes incl. AI.
4. `remediator/reporter.py` + `backend/cli.py` — end-to-end audit→fix→report on PPTX via CLI.
5. `remediator/rules/pdf_rules.py` + `handlers/pdf_handler.py` + `fixers/pdf_fixer.py` — PDF incl. OCR.
6. `backend/app/` — auth (mock first), storage service, job runner, routes.
7. `frontend/` — sign-in, file explorer, upload, status polling, report viewer, sign-off modal.
8. `AzureOIDCProvider` — wire real Temple SSO once IT approval lands.

---

## Deployment
<!-- Full detail in ai_specs/deployment.md -->

Primary target is **Render** (FastAPI web service + static frontend build + a persistent disk mounted for `STORAGE_DIR`), with the **Temple data center** as the alternative if access and approval are obtained. No database to provision. OCR requires Tesseract installed in the backend image.
