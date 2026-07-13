"""LLM providers for alt text and slide titles.

Two providers are supported — selected automatically from ``LLM_BASE_URL``:

* ``OpenAICompatibleProvider`` — any endpoint that speaks ``/chat/completions``
  (OpenAI, Groq, local Ollama, etc.). Default.
* ``AnthropicProvider`` — Anthropic's ``/v1/messages`` API (Claude / Fable 5).
  Auto-selected when ``LLM_BASE_URL`` contains "anthropic.com".

Swap providers by setting ``LLM_BASE_URL`` / ``LLM_MODEL`` in ``.env``.
No vendor SDK is hard-coded — plain HTTP only.

Failures raise :class:`LLMError`; the caller (``ai_fixer``) degrades to a
placeholder so a remediation job always finishes.
"""

from __future__ import annotations

import base64
import io
import json
import os
from dataclasses import dataclass

import httpx

from remediator.config import LLMConfig
from remediator.llm import prompts


@dataclass
class CaptionResult:
    alt_text: str
    decorative: bool
    confidence: float


@dataclass
class TitleResult:
    title: str
    confidence: float


class LLMError(Exception):
    """Raised when the LLM call fails or returns unusable output."""


def _strip_json(content: str) -> dict:
    """Parse a JSON object from model output, tolerating ```json fences."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise LLMError(f"Malformed JSON from LLM: {content!r}") from exc


def _resize_image(image_bytes: bytes, max_kb: int) -> tuple[bytes, str]:
    """Downscale/re-encode an image to roughly ``max_kb`` for cost/latency."""
    if len(image_bytes) <= max_kb * 1024:
        return image_bytes, "image/png"
    try:
        from PIL import Image
    except ImportError:
        return image_bytes, "image/png"

    img = Image.open(io.BytesIO(image_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    for scale in (1.0, 0.75, 0.5, 0.35):
        if scale < 1.0:
            w, h = img.size
            resized = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        else:
            resized = img
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=85)
        data = buf.getvalue()
        if len(data) <= max_kb * 1024:
            return data, "image/jpeg"
    return data, "image/jpeg"  # best effort


class OpenAICompatibleProvider:
    """Minimal OpenAI-compatible chat client (vision-capable)."""

    def __init__(self, api_key: str, base_url: str, model: str, cfg: LLMConfig):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.cfg = cfg

    def _chat(self, messages: list[dict]) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.cfg.max_output_tokens,
            "temperature": 0,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        last_exc: Exception | None = None
        for _ in range(2):  # one retry on transient failure
            try:
                resp = httpx.post(
                    url, json=payload, headers=headers, timeout=self.cfg.timeout_seconds
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except (httpx.HTTPError, KeyError, IndexError) as exc:
                last_exc = exc
        raise LLMError(f"LLM request failed: {last_exc}") from last_exc

    def caption_image(
        self, image_bytes: bytes, mime_type: str = "image/png", context: str = ""
    ) -> CaptionResult:
        data, mime = _resize_image(image_bytes, self.cfg.max_image_size_kb)
        b64 = base64.b64encode(data).decode("ascii")
        data_url = f"data:{mime};base64,{b64}"
        messages = prompts.build_alt_text_messages(data_url, context)
        parsed = _strip_json(self._chat(messages))
        return CaptionResult(
            alt_text=str(parsed.get("alt_text", "")).strip(),
            decorative=bool(parsed.get("decorative", False)),
            confidence=float(parsed.get("confidence", 0.0)),
        )

    def suggest_title(self, slide_text: str) -> TitleResult:
        messages = prompts.build_title_messages(slide_text)
        parsed = _strip_json(self._chat(messages))
        return TitleResult(
            title=str(parsed.get("title", "")).strip(),
            confidence=float(parsed.get("confidence", 0.0)),
        )


class AnthropicProvider:
    """Anthropic Messages API provider (Claude / Fable 5).

    Auto-selected when ``LLM_BASE_URL`` contains ``anthropic.com``.
    Uses ``x-api-key`` auth and the ``/v1/messages`` endpoint.
    """

    def __init__(self, api_key: str, base_url: str, model: str, cfg: LLMConfig):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.cfg = cfg

    def _chat(self, system: str, user_content: list[dict]) -> str:
        url = f"{self.base_url}/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": self.cfg.max_output_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user_content}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        last_exc: Exception | None = None
        for _ in range(2):
            try:
                resp = httpx.post(
                    url, json=payload, headers=headers, timeout=self.cfg.timeout_seconds
                )
                resp.raise_for_status()
                data = resp.json()
                return data["content"][0]["text"]
            except (httpx.HTTPError, KeyError, IndexError) as exc:
                last_exc = exc
        raise LLMError(f"Anthropic request failed: {last_exc}") from last_exc

    def caption_image(
        self, image_bytes: bytes, mime_type: str = "image/png", context: str = ""
    ) -> CaptionResult:
        data, mime = _resize_image(image_bytes, self.cfg.max_image_size_kb)
        b64 = base64.b64encode(data).decode("ascii")
        # Anthropic uses "image" content type with base64 source
        user_content: list[dict] = []
        if context:
            user_content.append({"type": "text", "text": f"Context: {context}"})
        user_content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": mime, "data": b64},
        })
        parsed = _strip_json(self._chat(prompts.ALT_TEXT_SYSTEM, user_content))
        return CaptionResult(
            alt_text=str(parsed.get("alt_text", "")).strip(),
            decorative=bool(parsed.get("decorative", False)),
            confidence=float(parsed.get("confidence", 0.0)),
        )

    def suggest_title(self, slide_text: str) -> TitleResult:
        user_content = [{"type": "text", "text": f"Slide text:\n{slide_text}"}]
        parsed = _strip_json(self._chat(prompts.TITLE_SYSTEM, user_content))
        return TitleResult(
            title=str(parsed.get("title", "")).strip(),
            confidence=float(parsed.get("confidence", 0.0)),
        )


def build_provider(cfg: LLMConfig, env: dict | None = None) -> OpenAICompatibleProvider | AnthropicProvider | None:
    """Construct a provider from config + environment.

    Auto-selects AnthropicProvider when LLM_BASE_URL contains "anthropic.com",
    otherwise uses OpenAICompatibleProvider.

    Returns ``None`` when the LLM is disabled or no API key is configured —
    the fixer then treats every alt-text/title issue as a placeholder.
    """
    env = env if env is not None else os.environ
    if not cfg.enabled:
        return None
    api_key = env.get("LLM_API_KEY")
    base_url = env.get("LLM_BASE_URL")
    model = env.get("LLM_MODEL")
    if not (api_key and base_url and model):
        return None
    if "anthropic.com" in base_url:
        return AnthropicProvider(api_key, base_url, model, cfg)
    return OpenAICompatibleProvider(api_key, base_url, model, cfg)
