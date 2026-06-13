"""Engine configuration.

Loads the non-secret ``config.yaml`` into typed dataclasses. Secrets (LLM API
key, base URL, model) are read from the environment by the LLM provider, not
from here. ``load_config()`` falls back to documented defaults so the engine
runs even with no ``config.yaml`` present (useful for tests and the CLI).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path

import yaml


@dataclass
class LLMConfig:
    enabled: bool = True
    generate_alt_text: bool = True
    suggest_titles: bool = True
    max_image_size_kb: int = 1024
    confidence_threshold: float = 0.6
    timeout_seconds: int = 60
    max_output_tokens: int = 200


@dataclass
class FixesConfig:
    auto_fix_minor: bool = True
    auto_fix_major: bool = True
    convert_old_format: bool = True


@dataclass
class SignoffConfig:
    add_placeholder_for_unfixable: bool = True
    placeholder_alt_text: str = "[Image — description pending instructor review]"
    placeholder_slide_title_prefix: str = "Slide"
    default_language: str = "en-US"


@dataclass
class ScoringConfig:
    severe_weight: int = 3
    major_weight: int = 2
    minor_weight: int = 1
    severe_cap: int = 20


@dataclass
class StorageConfig:
    max_file_size_mb: int = 50


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    fixes: FixesConfig = field(default_factory=FixesConfig)
    signoff: SignoffConfig = field(default_factory=SignoffConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)


def _build(cls, data: dict | None):
    """Instantiate a dataclass from a dict, ignoring unknown keys."""
    data = data or {}
    known = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in known})


def load_config(path: str | os.PathLike | None = None) -> Config:
    """Load configuration from ``config.yaml``.

    Search order: explicit ``path`` -> ``$A11Y_CONFIG`` -> ``config.yaml`` at
    the repository root (two levels up from this file). Missing file or keys
    fall back to defaults.
    """
    if path is None:
        path = os.environ.get("A11Y_CONFIG")
    if path is None:
        candidate = Path(__file__).resolve().parents[1] / "config.yaml"
        path = candidate if candidate.exists() else None

    data: dict = {}
    if path and Path(path).exists():
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

    return Config(
        llm=_build(LLMConfig, data.get("llm")),
        fixes=_build(FixesConfig, data.get("fixes")),
        signoff=_build(SignoffConfig, data.get("signoff")),
        scoring=_build(ScoringConfig, data.get("scoring")),
        storage=_build(StorageConfig, data.get("storage")),
    )
