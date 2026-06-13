# Features

> **OpenOwls SDD** — Read by end users and the product owner.
> Defines what the application does, written in plain language.
> Organized into three phases. Phase 1 is the MVP — it must be achievable in the first sprint.

---

## How to Read This File

- **Phase 1** — Must-have features. The app is not usable without these.
- **Phase 2** — Should-have features. Adds meaningful value once Phase 1 is stable.
- **Phase 3** — Nice-to-have features. Advanced capabilities, AI enhancements, or stretch goals.

Each feature includes a short description and a set of acceptance criteria written from the user's perspective.

---

## Phase 1 — Core MVP
<!-- Faculty defines this phase. Focus on the smallest useful version of the app. -->

### Feature 1: Temple-only sign-in

**As a** Temple faculty member,
**I want to** sign in so that only Temple users can access the app and I get my own private workspace,
**So that** my course materials are kept separate from everyone else's and access is restricted to my institution.

**Notes:** Authentication sits behind a swappable interface. A **dev/mock login** (enter an email, get the matching workspace) is used for local development. The production provider is **Microsoft Azure AD / Temple SSO (OAuth2 / OIDC)**, which redirects to the Temple University login. Wiring up real Azure SSO is an early Phase 1 task that depends on Temple IT approval (app registration, redirect URIs, client secret, tenant restriction) and is **not a hard blocker** for the rest of Phase 1.

**Acceptance Criteria:**
- [ ] Given I am not signed in, when I open the app, then I am prompted to sign in and cannot see any files.
- [ ] Given I sign in (mock in dev, Azure SSO in production), when authentication succeeds, then I land on my personal home page.
- [ ] Given the production provider is active, when a non-Temple account attempts to sign in, then access is denied.
- [ ] Given I am signed in, when my workspace is created, then a folder keyed by my email username exists with `input/` and `output/` subfolders.

---

### Feature 2: Personal workspace home page

**As a** signed-in faculty member,
**I want to** see my profile and browse my files in one place,
**So that** I can manage my uploaded and remediated materials easily.

**Notes:** The home page has a **top panel** showing the user's name and email address, and a **bottom panel** that behaves like a file explorer (Windows Explorer–style) listing the user's files and groups. An **Upload** button sits in the top-right of the file panel and starts the upload workflow.

**Acceptance Criteria:**
- [ ] Given I am signed in, when the home page loads, then the top panel shows my name and email.
- [ ] Given I have uploaded files, when I view the bottom panel, then I see my groups and the files inside them, organized by `input/` and `output/`.
- [ ] Given I am on the home page, when I look at the top-right of the file panel, then I see an Upload button.
- [ ] Given a remediated output file exists, when I view it in the explorer, then I can download it.

---

### Feature 3: Upload files grouped by name

**As a** faculty member,
**I want to** upload a set of files under a group name (usually the course code),
**So that** my materials stay organized by course.

**Notes:** Files are stored at `input/<group>/<filename>` (e.g. `input/CIS4526/lecture1.pptx`). Phase 1 accepts **PPTX and PDF** only.

**Acceptance Criteria:**
- [ ] Given I click Upload, when I am prompted, then I can enter/choose a group name (e.g. a course code) and select one or more files.
- [ ] Given I select files, when I confirm, then each file is saved under `input/<group>/`.
- [ ] Given I upload an unsupported file type, when I confirm, then the app rejects it with a clear message (only PPTX and PDF allowed in Phase 1).
- [ ] Given an upload completes, when I return to the file explorer, then the new group and files appear.

---

### Feature 4: Automated remediation ("Fix" button)

**As a** faculty member,
**I want to** click a Fix button to automatically remediate my uploaded files,
**So that** I don't have to fix accessibility issues by hand.

**Notes:** The backend processes files **one at a time**. For each input file it produces a remediated copy with an `_a11y` tag in the filename, stored in the output folder. Example: `input/CIS4526/lecture1.pptx` → `output/CIS4526/lecture1_a11y.pptx`. The `_a11y` suffix marks the file as the remediated version.

The remediation engine targets these WCAG-related document checks in Phase 1:

| Check | What the engine does |
|-------|----------------------|
| Image alt text | Generate best-effort alt text with the vision LLM; mark purely decorative images as decorative |
| Slide titles (PPTX) / document title (PDF) | Detect missing titles and generate/set them |
| Document language | Detect and set the document language |
| Color contrast | Detect text/background contrast below threshold; adjust where safely possible, otherwise flag for review |
| Table headers | Mark header rows so tables read correctly |
| Link text | Replace bare/duplicate URLs with descriptive link text where possible |
| Reading order | Set a sensible reading/tab order for slide objects (best-effort) |

**Acceptance Criteria:**
- [ ] Given I have uploaded files in a group, when I click Fix, then the backend remediates each file one at a time.
- [ ] Given a file is remediated, when processing finishes, then a corresponding `<name>_a11y.<ext>` file appears under `output/<group>/`.
- [ ] Given remediation runs, when it completes, then the output file is still valid and opens correctly in PowerPoint / Acrobat.
- [ ] Given an input file is already accessible, when I run Fix, then the output file is produced without breaking existing content.

---

### Feature 5: Internal accessibility checker and score

**As a** faculty member,
**I want to** see a before/after accessibility score for each file,
**So that** I can trust that remediation worked before I re-upload to Canvas.

**Notes:** Because Phase 1 is standalone and does not talk to Canvas or the vendor, the app includes its own lightweight **WCAG-approximating checker** that scores a file out of 100. It scores the original input and the remediated output so the improvement is visible. The real confirmation still happens when the file is re-uploaded to Canvas.

**Acceptance Criteria:**
- [ ] Given a file is uploaded, when it is scanned, then the app reports an accessibility score out of 100 and the list of detected issues.
- [ ] Given a file is remediated, when scanning the output, then the app reports the new score and which issues were resolved.
- [ ] Given remediation is successful, when I view the result, then the output score is at or near 100.

---

### Feature 6: Best-effort "pass the checker" mode

**As a** faculty member,
**I want to** have the app make a file pass the checks even when it can't truly fix an issue,
**So that** Canvas reports the file as accessible and I am given a punch-list to finish manually.

**Notes:** When the engine (or the LLM) cannot confidently fix an issue, it still makes the issue **pass** — by inserting a placeholder value or marking a decorative image as decorative — rather than leaving a failure. Every placeholder is recorded for human follow-up. This is the deliberate "checker-passing vs. genuinely accessible" trade-off described in `domain-knowledge.md`.

**Acceptance Criteria:**
- [ ] Given the LLM cannot confidently caption an image, when remediation runs, then a placeholder is written and the item is flagged "needs human follow-up."
- [ ] Given placeholders were used, when I view the score, then the file passes the checker even though some items are placeholders.
- [ ] Given placeholders were used, when I read the report, then placeholder items are clearly separated from genuinely-fixed items.

---

### Feature 7: AI-generated alt text and titles

**As a** faculty member,
**I want to** have the app describe my images and name my untitled slides automatically,
**So that** I don't have to write alt text and titles by hand.

**Notes:** A **vision-capable LLM**, accessed through an OpenAI-compatible interface, generates draft alt text for images and titles for untitled slides/documents. Provider/model is swappable. Details of prompts, confidence handling, and evaluation live in `llm-integration.md`.

**Acceptance Criteria:**
- [ ] Given an image has no alt text, when remediation runs, then the LLM produces a concise, relevant description that is written into the file.
- [ ] Given a slide has no title, when remediation runs, then a short descriptive title is generated and set.
- [ ] Given the LLM returns low-confidence output, when remediation runs, then the item is treated as a placeholder and flagged for review.

---

### Feature 8: Remediation report

**As a** faculty member,
**I want to** see a detailed report of what was changed in each file,
**So that** I know what was genuinely fixed and what I still need to revisit manually.

**Notes:** The report separates **genuinely-fixed** items from **placeholder / needs-review** items, and may surface two numbers — a checker-passing score and a "truly remediated" estimate — to keep the tool honest.

**Acceptance Criteria:**
- [ ] Given remediation finishes, when I open the report, then I see a per-file list of every change made.
- [ ] Given placeholders were used, when I read the report, then those items are in a distinct "needs human follow-up" section.
- [ ] Given I want a record, when I view the report, then I can download or export it alongside the remediated file.

---

## Phase 2 — Enhanced Features
<!-- Students define this phase after Phase 1 is complete and reviewed. -->

### Feature 9: Additional file formats (Word, and beyond)

**As a** faculty member,
**I want to** remediate Word documents (and, later, other formats),
**So that** the tool covers more of my course materials.

**Acceptance Criteria:**
- [ ] Given a `.docx` file, when I run Fix, then it is remediated and a `_a11y.docx` output is produced.
- [ ] Given the format-handler design from Phase 1, when a new format is added, then no changes to the core pipeline are required beyond a new handler.

---

### Feature 10: Video accessibility

**As a** faculty member,
**I want to** generate captions/transcripts for lecture videos,
**So that** video content is accessible too.

**Acceptance Criteria:**
- [ ] Given a supported video file, when I run Fix, then a caption/transcript file is produced.

---

### Feature 11: Batch / whole-course processing

**As a** faculty member,
**I want to** remediate an entire group of files at once,
**So that** I can process a whole course in one action.

**Acceptance Criteria:**
- [ ] Given a group with multiple files, when I click Fix on the group, then all files are remediated and outputs appear together.
- [ ] Given a long-running batch, when processing, then I can see progress per file.

---

### Feature 12: Human-in-the-loop review

**As a** faculty member,
**I want to** review and edit the AI's suggested alt text and titles before they are written,
**So that** I can correct anything the AI got wrong.

**Acceptance Criteria:**
- [ ] Given the LLM produced draft alt text/titles, when I open the review screen, then I can approve or edit each suggestion before it is applied.
- [ ] Given I edit a suggestion, when I save, then the edited value is written into the output file.

---

## Phase 3 — Advanced / AI Features
<!-- Students define this phase. Typically includes LLM-powered capabilities. -->

### Feature 13: Canvas and vendor (Panorama / Ally) integration

**As a** faculty member,
**I want to** connect the app to Canvas so it can pull my course files, read the vendor's real accessibility scores and issue lists, remediate, and push the fixed files back,
**So that** I never have to manually upload or download anything.

**Acceptance Criteria:**
- [ ] Given Canvas API access, when I select a course, then the app lists that course's files.
- [ ] Given the vendor exposes results, when a file is scanned, then the app reads the real score and issue list rather than only its internal checker.
- [ ] Given remediation completes, when I confirm, then the remediated file is pushed back into Canvas.

---

## Out of Scope
<!-- Features that were considered but explicitly excluded. Helps prevent scope creep. -->

- Native mobile app (web only).
- Remediating Canvas pages, quizzes, or other non-document course content.
- Any legal guarantee or certification of full WCAG / ADA / Section 508 conformance.
- Role-based permissions, admin dashboards, or sharing workspaces between users (Phase 1).
- Persistent history, analytics, or accounts beyond per-user file folders (Phase 1).
