from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Mapping

import httpx


@dataclass(frozen=True, slots=True)
class OpenAICompatibleConfig:
    """Configuration for an OpenAI-compatible Chat Completions endpoint."""

    base_url: str
    api_key: str
    model: str
    timeout_seconds: float


def load_openai_compatible_config() -> OpenAICompatibleConfig | None:
    """Load OpenAI-compatible LLM config from environment variables."""
    base_url = os.getenv("AI_ASSISTANTS_LLM_BASE_URL")
    api_key = os.getenv("AI_ASSISTANTS_LLM_API_KEY")
    model = os.getenv("AI_ASSISTANTS_LLM_MODEL")
    if not base_url or not api_key or not model:
        return None
    timeout_raw = os.getenv("AI_ASSISTANTS_LLM_TIMEOUT_SECONDS", "10")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 10.0
    return OpenAICompatibleConfig(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    )


class OpenAICompatibleClient:
    """Minimal client for OpenAI-compatible chat completions."""

    def __init__(self, config: OpenAICompatibleConfig, client: httpx.Client | None = None) -> None:
        self._config = config
        self._client = client or httpx.Client(timeout=config.timeout_seconds)

    def chat_completion(self, *, system: str, user: str) -> str:
        """Call the chat completions endpoint and return the assistant content."""
        url = f"{self._config.base_url}/v1/chat/completions"
        resp = self._client.post(
            url,
            headers={"Authorization": f"Bearer {self._config.api_key}"},
            json={
                "model": self._config.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, Mapping):
            raise ValueError("Invalid LLM response: expected object")
        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            raise ValueError("Invalid LLM response: missing choices")
        first = choices[0]
        if not isinstance(first, Mapping):
            raise ValueError("Invalid LLM response: invalid choice")
        message = first.get("message")
        if not isinstance(message, Mapping):
            raise ValueError("Invalid LLM response: missing message")
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("Invalid LLM response: missing content")
        return content


