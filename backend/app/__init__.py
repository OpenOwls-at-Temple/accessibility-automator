"""FastAPI web layer for Accessibility Automator.

Thin orchestration over the ``remediator`` engine: authentication, per-user
file storage, and background remediation jobs. The LLM is only ever called
server-side, inside the engine. This package MAY import ``remediator``; the
engine never imports back.
"""
