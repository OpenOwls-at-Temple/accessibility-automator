# LLM Integration

> **OpenOwls SDD** — Read by engineers and the AI coding assistant.
> Every OpenOwls project has an LLM layer. This file defines what the LLM is responsible for,
> how it is integrated, how prompts are designed, and how the results are evaluated.
> Treat the LLM as a first-class component of the system — not an afterthought.

---

## What the LLM Does in This App
<!-- Describe clearly what role the LLM plays. -->

The LLM solves the parts of accessibility remediation that are **judgment calls, not mechanical edits**. Setting a language flag or marking a table header is deterministic code; *describing what an image shows* or *naming an untitled slide* requires understanding content — which is what the LLM provides.

| Responsibility | Description |
|----------------|-------------|
| **Image alt text** | Given an image (a photo, chart, diagram, screenshot) from a slide or PDF, produce a concise, meaningful description to write as alt text. (Checks **P3**, **D3**.) |
| **Slide / document titles** | Given the text content of an untitled slide (or PDF section), produce a short, descriptive title. (Check **P2**.) |
| **Decorative-image hint** *(optional)* | Help decide whether an image is purely decorative (and should be marked decorative) versus informative (and needs alt text). |

The LLM does **not** decide scores, does not fix contrast/fonts, and is never the sole arbiter of accessibility — its outputs are drafts that either pass with confidence or fall back to a flagged placeholder.

---

## Model

| Setting | Value |
|---------|-------|
| Provider | **Two providers supported** — auto-selected from `LLM_BASE_URL` (see below) |
| Model | A **vision-capable** chat model. Set via `LLM_MODEL`. |
| Why this design | Alt text requires true image captioning. The provider interface lets us swap model/vendor by changing `.env` only — no code change. |
| Called from | Server-side only — `remediator/fixers/ai_fixer.py`. The frontend never calls the LLM directly. |
| API key / endpoint | Server-side env vars: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`. |

### Supported Providers (auto-detected from `LLM_BASE_URL`)

| Provider | `LLM_BASE_URL` | `LLM_MODEL` example | Auth header |
|----------|---------------|---------------------|-------------|
| **Anthropic** (Claude / Fable 5) ← recommended | `https://api.anthropic.com` | `claude-fable-5` | `x-api-key` |
| **OpenAI-compatible** (OpenAI, Groq, Ollama…) | `https://api.openai.com/v1` | `gpt-4o-mini` | `Bearer` |

`build_provider()` in `remediator/llm/provider.py` checks if `"anthropic.com"` is in `LLM_BASE_URL` and returns the matching class. No other changes needed.

### To use Fable 5 — set these 3 lines in `.env`
```
LLM_API_KEY=sk-ant-...
LLM_BASE_URL=https://api.anthropic.com
LLM_MODEL=claude-fable-5
```

---

## Prompts
<!-- All prompts live in remediator/llm/prompts.py — never inline in fixers or routes. -->

### Prompt 1: Image Alt Text

**Purpose:** Produce concise, accurate alt text for an image so screen-reader users understand its content/purpose.

**System Prompt:**
```
You are an accessibility expert writing alt text for images in university lecture
materials, following WCAG 2.1 guidance. Describe the image's content and purpose
clearly and concisely.

Rules:
- 1–2 sentences, ideally under 125 characters. Be specific, not generic.
- Do NOT begin with "image of" or "picture of".
- If the image is a chart/graph, state the chart type and its main takeaway.
- If the image contains text, include the essential text.
- If the image appears purely decorative (no informational content), set
  "decorative": true and leave "alt_text" empty.
- Report your confidence from 0.0 to 1.0. If you cannot tell what the image
  shows, give low confidence rather than guessing.
- Respond in JSON only.
```

**User Input:**
```
The image (as image input) plus optional context: the slide title, nearby slide
text, and the file/course name — to help disambiguate (e.g. a chart's subject).
```

**Expected Output Format:**
```json
{ "alt_text": "string", "decorative": false, "confidence": 0.0 }
```

**Notes:**
- Resize images larger than `max_image_size_kb` before sending (cost/latency).
- If `confidence < confidence_threshold` (config, default 0.6) → treat as a **placeholder** and flag for review; do not write low-confidence text as if it were a real fix.

---

### Prompt 2: Slide / Section Title

**Purpose:** Generate a short descriptive title for a slide or PDF section that has none.

**System Prompt:**
```
You are helping make lecture slides accessible. Given the text content of a slide
that has no title, write a short, descriptive title (2–6 words) that captures the
slide's main topic. Do not invent content not implied by the text. Report a
confidence from 0.0 to 1.0. Respond in JSON only.
```

**User Input:**
```
The visible text of the slide (bullet points, body text). If the slide has almost
no text, send what is available.
```

**Expected Output Format:**
```json
{ "title": "string", "confidence": 0.0 }
```

**Notes:**
- If the slide has essentially no text, or confidence is low → use the placeholder `"Slide {N}"` and flag it.

---

## Architecture

- **Prompt definitions:** `remediator/llm/prompts.py`
- **LLM provider/client:** `remediator/llm/provider.py` (OpenAI-compatible)
- **Called by:** `remediator/fixers/ai_fixer.py`, invoked by the pipeline during the fix step
- **Frontend interaction:** none directly — the frontend triggers `/api/v1/groups/{group}/remediate`; all LLM work happens server-side inside the job.

### Call Flow
```
User clicks "Fix" (frontend)
  → POST /api/v1/groups/{group}/remediate  → background job
    → pipeline: audit → for each fixable image/title issue
      → ai_fixer → LLMProvider (build prompt, send image/text, call endpoint)
        → parse + validate JSON, check confidence
          → high confidence: write value (alt text / title)
          → low confidence / failure: write placeholder, record sign-off
    → re-audit, score, write report
  → frontend polls /jobs/{id}, then shows report
```

---

## Context & Token Management

| Concern | Decision |
|---------|----------|
| Images per file | One LLM call per image needing alt text; one per untitled slide |
| Image size | Downscale to ≤ `max_image_size_kb` (default 1024 KB) before sending |
| Max output tokens | Small (~150) — outputs are short alt text/titles |
| Batching | Process one file at a time; images sequentially (simpler, predictable cost). Parallelization is a Phase 2 optimization. |
| Cost stance | Cost is tracked but **not artificially capped**. Log per-call and per-file token usage so spend is visible and the model choice can be tuned. |
| Excluded from context | Never send the whole document — only the single image plus minimal surrounding text. |

---

## Error Handling & Fallbacks

| Scenario | Handling |
|----------|----------|
| API timeout | Retry once after a short backoff, then write a placeholder and flag for review |
| Malformed JSON | Attempt one reparse/retry; on failure, placeholder + flag; log raw response |
| Rate limit (429) | Backoff and retry with a cap; if still failing, placeholder the remaining items so the job completes |
| Low-confidence output | Treat as placeholder (do not present as a real fix) |
| LLM disabled (`llm.enabled: false`) | Skip AI fixes entirely; all alt-text/title issues become placeholders |

The guiding rule: **a remediation job must always finish and produce a valid output file**, even if every LLM call fails — failures degrade to placeholders, never crashes.

---

## Privacy & Safety

- **Sent to LLM:** image contents and small snippets of slide/section text from faculty-uploaded course materials, plus the file/course name for context.
- **Never sent to LLM:** user identity beyond what's needed, passwords/secrets, and (per project scope) any **student data** — the app handles only faculty course materials.
- **Data retention:** confirm the chosen provider's policy; prefer endpoints that **do not train on inputs**. Document the active provider's stance in `deployment.md`.
- **Content safety:** course images are generally benign, but the pipeline must handle unexpected/empty model output gracefully (see fallbacks). Course materials may be copyrighted by the instructor — they stay within the user's workspace and the LLM call; they are not stored or reused elsewhere.

---

## Evaluation

| Metric | How to Measure | Target |
|--------|----------------|--------|
| Alt-text usefulness | Human review of ~20 sample images (good fixtures + real slides) | ≥ 80% rated accurate & useful by reviewers |
| Title relevance | Human review of generated titles vs slide content | ≥ 80% rated appropriate |
| JSON parse success | Logged in `ai_fixer` | ≥ 98% |
| Placeholder rate | Share of AI items that fell back to placeholder | Tracked; lower is better (signals model/prompt quality) |
| Confidence calibration | Spot-check that low-confidence outputs really were the weak ones | Qualitative |
| Per-file LLM cost | Logged token usage × price | Tracked for budgeting |

Evaluation uses the same `remediator/tests/fixtures/` images (known-bad/known-good) plus a small human-rated sample, since alt-text quality cannot be fully automated.

---

## Prompt Iteration Log

| Date | Prompt | Change Made | Reason |
|------|--------|-------------|--------|
| 2026-06-13 | Alt Text | Initial version | Baseline: concise, decorative detection, confidence score, JSON-only |
| 2026-06-13 | Title | Initial version | Baseline: 2–6 word titles, confidence score, JSON-only |
