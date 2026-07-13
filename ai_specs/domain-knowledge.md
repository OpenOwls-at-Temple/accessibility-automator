# Domain Knowledge

> **OpenOwls SDD** — Read primarily by the AI coding assistant.
> Captures domain-specific concepts, terminology, business rules, and constraints
> that are not obvious from the code itself. Faculty seeds this file; students expand it.

---

## Domain Overview
<!-- What domain does this application operate in? Give a brief description. -->

This application operates in the **digital accessibility** domain for higher education. Temple University faculty upload lecture materials (primarily PowerPoint and PDF) to **Canvas**, the university's Learning Management System (LMS). Canvas is integrated with **YuJa Panorama**, a third-party accessibility platform that automatically scans each uploaded file, scores it against the **WCAG** standard, flags specific accessibility issues, and offers tools to fix them.

Accessibility Automator is a standalone tool that **remediates these same files before (or instead of) the manual fix-up in Canvas**, so that when a faculty member uploads the remediated file, Panorama reports it as highly accessible (a score at or near 100). The app must therefore understand the same WCAG checks that Panorama evaluates, and approximate them in its own internal checker.

---

## Key Concepts & Terminology
<!-- Define terms that have a specific meaning in this domain. -->

| Term | Definition |
|------|------------|
| **WCAG** | Web Content Accessibility Guidelines — the international standard (W3C) for digital accessibility. The relevant target is **WCAG 2.1 / 2.2 Level AA**, which Panorama, ADA, and Section 508 all align to. (The user may informally call this "WAOG.") |
| **Level AA** | The conformance level most institutions (and Panorama's default scoring) target. Stricter than A, less strict than AAA. |
| **Canvas** | The Learning Management System Temple uses. Faculty upload course materials here. |
| **YuJa Panorama** | The third-party accessibility platform integrated into Temple's Canvas via **LTI 1.1 / 1.3**. It scans files, assigns an accessibility score, lists issues, offers inline remediation and 20+ "alternative formats." This is the checker our app must satisfy. |
| **Anthology Ally** | A competing accessibility tool that many other universities use. Conceptually similar to Panorama (weighted WCAG scoring, color gauge). Temple uses Panorama, but the architecture should not hard-code assumptions specific to either vendor. |
| **Accessibility Score** | A 0–100 rating of how accessible a file is. Computed as a **weighted average** of individual WCAG checks, where more severe issues lower the score more. Panorama shows it as a color-coded smiley icon (red / yellow / green). |
| **Score bands** | Red / "needs help" ≈ 0–33; Yellow / "a little better" ≈ 34–66; Green / "almost there" ≈ 67–99; Perfect = 100. (These mirror the well-documented Ally bands and Panorama's color icons.) |
| **Remediation** | The act of fixing accessibility issues in a document (adding alt text, titles, tags, etc.). |
| **Alt text** | A short text description of an image, read aloud by screen readers. Required for all meaningful images. |
| **Decorative image** | An image that conveys no information (borders, background flourishes). The correct fix is to **mark it decorative** (so it is skipped by screen readers) rather than to write alt text. |
| **Reading order** | The sequence in which a screen reader announces content. Must follow the logical order, not the visual layout. |
| **Tagged PDF** | A PDF containing a structure tree (tags for headings, paragraphs, lists, tables, figures) that assistive technology relies on. Untagged PDFs are largely inaccessible. |
| **`_a11y` suffix** | The project's naming convention for a remediated output file. `a11y` is the standard numeronym for "accessibility" (a + 11 letters + y). Example: `lecture1.pptx` → `lecture1_a11y.pptx`. |
| **Group** | A user-chosen name (usually a course code, e.g. `CIS4526`) that organizes a batch of uploaded files into a folder. |
| **Placeholder fix** | A value written purely to make a check pass when the app cannot produce a truly correct value. It satisfies the checker but still needs human follow-up. |

---

## The WCAG Checks the App Must Handle
<!-- The concrete document checks Panorama-style tools evaluate, and how our app addresses each. -->

| Check | Why it matters | Phase 1 remediation approach |
|-------|----------------|------------------------------|
| **Image alt text** | Screen readers need a description of every meaningful image | LLM-generated alt text; mark purely decorative images decorative |
| **Slide titles (PPTX) / document title (PDF)** | Titles let users navigate between slides/sections | Detect missing titles; generate and set them |
| **Document language** | Tells the screen reader which pronunciation rules / voice to use | Detect and set the document's language attribute |
| **Color contrast** | Low contrast text is unreadable for low-vision users. AA requires **4.5:1** for normal text, **3:1** for large text (≥18pt, or ≥14pt bold) | Detect failing text; adjust color where safe, otherwise flag for review |
| **Headings / structure** | Proper heading levels (not just bold/large text) enable navigation | Detect and apply real heading styles; for PDF, ensure tagged structure |
| **Table headers** | Header rows/cells let screen readers associate data with labels | Mark header rows so tables read correctly |
| **Link text** | Bare URLs and "click here" give no context out of context | Replace non-descriptive link text with meaningful text where possible |
| **Reading order** | Out-of-order content is confusing or nonsensical when read aloud | Set a sensible reading/tab order (best-effort, especially for slides) |
| **Tagged PDF / scanned PDF** | Untagged or image-only (scanned) PDFs are unreadable by AT | Add structure tags; OCR scanned PDFs so text is present (harder — may be partly Phase 2) |

---

## Business Rules
<!-- Rules that must always be enforced, regardless of implementation details. -->

- Each user can only see and operate on **their own files**, stored under a folder keyed by their email username.
- Every remediated file is written to the `output/` folder with the **`_a11y` suffix**; the original input file in `input/` is **never modified or deleted**.
- The internal checker must score **both the original input and the remediated output**, so the before/after improvement is always visible.
- When an issue cannot be confidently fixed, the app must still make it **pass the checker** (placeholder value or mark-decorative) AND record it as **"needs human follow-up."**
- The remediation report must **clearly separate genuinely-fixed items from placeholder items**. The app must never present a placeholder as a real fix.
- Output files must remain **valid and openable** in PowerPoint / Acrobat and re-uploadable to Canvas.
- The app must **not store student data** — only faculty-uploaded course materials (FERPA-aware).

---

## Domain Constraints
<!-- Technical or domain limitations the AI should be aware of. -->

- **"Checker-passing" ≠ "genuinely accessible."** A placeholder alt text like "image" will satisfy Panorama's automated check but does not actually help a screen-reader user. The app's honesty about this distinction (via the report and an optional "truly remediated" number) is a core design value, not an afterthought.
- **Panorama is not perfect.** Temple's own guidance notes that PDFs in particular often have accessibility issues Panorama does **not** flag, so a green icon does not guarantee true accessibility. Our internal checker is therefore an *approximation* of Panorama's behavior, not an exact reproduction — the real score only comes from re-uploading to Canvas.
- **Scoring is a weighted average** with configurable severity weights (critical / major / minor). Our internal scorer should use a documented, weighted model rather than a naive pass/fail count, so its scores roughly track Panorama's.
- **PDF remediation is genuinely hard** (tagging, reading order, OCR of scanned pages). Expect more placeholder / needs-review items for PDFs than for PPTX, and consider deferring the hardest PDF cases to Phase 2.
- The LLM must be called **server-side only** and sit behind an **OpenAI-compatible interface** so the model/provider is swappable.

---

## Common Pitfalls
<!-- Things that are easy to get wrong in this domain. -->

- Do not write alt text for **decorative** images — mark them decorative instead. Adding alt text to decorative images is itself an accessibility problem.
- Do not confuse **passing the checker** with **fixing the content**. Track them separately.
- Do not modify or overwrite the user's **original input file**. Always write a new `_a11y` output.
- Alt text should be **concise and meaningful** (describe the content/purpose), not a verbose dump or a filename.
- Setting a real **heading style** is different from making text bold/large — only the former is navigable.
- Contrast fixes can unintentionally change a slide's branding/design; adjust conservatively and flag rather than guess aggressively.
- Don't assume the vendor is Ally — Temple uses **Panorama**; keep vendor-specific logic out of the core engine (relevant for the Phase 3 integration).

---

## External Dependencies & Integrations
<!-- Any third-party services, APIs, or data sources this app depends on. -->

| Service | Purpose | Notes |
|---------|---------|-------|
| Vision-capable LLM (via OpenAI-compatible API) | Generate alt text and slide/document titles | Provider swappable; called server-side only; cost is a real consideration |
| Google SSO (Google Identity Services) + admin invite allowlist | Restrict access to added Temple accounts; per-user workspaces | Production auth; needs a Google OAuth web client ID. Dev uses a local dev-login. |
| Canvas LMS API *(Phase 3 only)* | Pull course files and push remediated files back | Not used in Phase 1 |
| YuJa Panorama *(Phase 3 only)* | Read the vendor's real scores / issue lists | Integrated into Canvas via LTI 1.1 / 1.3; not used in Phase 1 |

---

## References
<!-- Links to any external documentation, papers, or resources relevant to this domain. -->

- [WCAG 2.2 (W3C Recommendation)](https://www.w3.org/TR/WCAG22/)
- [Accessible Temple — Center for the Advancement of Teaching](https://teaching.temple.edu/accessible-temple)
- [Temple EDVICE EXCHANGE — All About YuJa's Panorama](https://sites.temple.edu/edvice/2025/07/17/your-accessibility-helper-all-about-yujas-panorama/)
- [YuJa Panorama — LMS Accessibility Platform](https://www.yuja.com/panorama/)
- [YuJa Panorama — Accessibility Scoring](https://www.yuja.com/panorama/accessibility-scoring/)
- [Integrating Panorama into Canvas Using LTI 1.3 (YuJa Help Center)](https://support.yuja.com/hc/en-us/articles/7955689760023-Integrating-Panorama-into-Canvas-Using-LTI-1-3)
- [Anthology Ally — Accessibility Scores (for comparison)](https://help.anthology.com/ally-lms/en/instructors/accessibility-scores.html)
