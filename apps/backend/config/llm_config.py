from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LLMConfig:
    """LLM configuration for OpenAI-compatible clients."""

    base_url: str | None
    api_key: str | None
    model: str | None
    timeout_seconds: float
    router_enabled: bool


def load_llm_config() -> LLMConfig:
    """Load LLM configuration from environment variables."""
    base_url = os.getenv("AI_ASSISTANTS_LLM_BASE_URL")
    api_key = os.getenv("AI_ASSISTANTS_LLM_API_KEY")
    model = os.getenv("AI_ASSISTANTS_LLM_MODEL")

    timeout_raw = os.getenv("AI_ASSISTANTS_LLM_TIMEOUT_SECONDS", "10")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 10.0
    timeout_seconds = max(1.0, timeout_seconds)

    router_enabled_raw = os.getenv("AI_ASSISTANTS_LLM_ROUTER_ENABLED", "0").strip().lower()
    router_enabled = router_enabled_raw in {"1", "true", "yes", "on"}

    return LLMConfig(
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
        router_enabled=router_enabled,
    )
