# testdata/ — local test decks (not committed)

Drop your own `.pptx` / `.pdf` files here to exercise the remediation engine by hand.

**Everything in this folder is gitignored except this README.** Nothing you place
here will be committed — see the `testdata/*` rule in `.gitignore`.

## Why this is local-only

- **Copyright / FERPA** — real lecture decks are faculty IP and may contain student
  information or licensed images. This is a shared org repo; anything committed is
  broadly visible and stays in git history permanently.
- **Repo bloat** — binaries balloon clone size and history forever.
- **Not needed for CI** — the automated test suite builds its own fixtures
  programmatically (`python-pptx` / `reportlab` in `remediator/tests/conftest.py`),
  so no sample binaries are required.

Keep **real** faculty/student content out of git entirely. If you ever need a
*reusable* fixture for automated tests, generate it in code (matching the existing
pattern) or commit only a **tiny, self-authored, synthetic** deck with deliberately
broken accessibility under `remediator/tests/fixtures/`.

## How to use these files

- **Through the app:** sign in (dev-login locally), create a group, upload a deck,
  click **Fix All**. Outputs land under `storage/users/<you>/output/<group>/…_a11y.<ext>`.
- **Standalone CLI:** run the engine's `fix` command directly against a file here for
  a faster iteration loop (no web layer). See `backend/cli.py`.
