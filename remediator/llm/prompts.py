"""All LLM prompts live here — never inline in fixers or routes.

See ai_specs/llm-integration.md for the rationale and the prompt iteration log.
Each builder returns the OpenAI-compatible ``messages`` list for a chat call.
"""

from __future__ import annotations

ALT_TEXT_SYSTEM = """\
You are an accessibility expert writing alt text for images in university lecture
materials, following WCAG 2.1 guidance. Describe the image's content and purpose
clearly and concisely.

Rules:
- 1-2 sentences, ideally under 125 characters. Be specific, not generic.
- Do NOT begin with "image of" or "picture of".
- If the image is a chart/graph, state the chart type and its main takeaway.
- If the image contains text, include the essential text.
- If the image appears purely decorative (no informational content), set
  "decorative": true and leave "alt_text" empty.
- Report your confidence from 0.0 to 1.0. If you cannot tell what the image
  shows, give low confidence rather than guessing.
- Respond in JSON only: {"alt_text": "string", "decorative": false, "confidence": 0.0}
"""

TITLE_SYSTEM = """\
You are helping make lecture slides accessible. Given the text content of a slide
that has no title, write a short, descriptive title (2-6 words) that captures the
slide's main topic. Do not invent content not implied by the text. Report a
confidence from 0.0 to 1.0. Respond in JSON only:
{"title": "string", "confidence": 0.0}
"""


def build_alt_text_messages(image_data_url: str, context: str = "") -> list[dict]:
    """Messages for image captioning. ``image_data_url`` is a base64 data URL."""
    user_content: list[dict] = []
    if context:
        user_content.append({"type": "text", "text": f"Context: {context}"})
    user_content.append({"type": "image_url", "image_url": {"url": image_data_url}})
    return [
        {"role": "system", "content": ALT_TEXT_SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_title_messages(slide_text: str) -> list[dict]:
    """Messages for slide-title suggestion from the slide's visible text."""
    return [
        {"role": "system", "content": TITLE_SYSTEM},
        {"role": "user", "content": f"Slide text:\n{slide_text}"},
    ]
