from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import httpx
from collections.abc import Mapping


class EmbeddingsProvider(Protocol):
    """Embeddings provider protocol."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for the provided texts."""


@dataclass(frozen=True, slots=True)
class OpenAICompatibleEmbeddingsConfig:
    """Config for OpenAI-compatible embeddings endpoint."""

    base_url: str
    api_key: str
    model: str
    timeout_seconds: float


def load_openai_compatible_embeddings_config() -> OpenAICompatibleEmbeddingsConfig | None:
    """Load embeddings config from env vars."""
    base_url = os.getenv("AI_ASSISTANTS_EMBEDDINGS_BASE_URL") or os.getenv("AI_ASSISTANTS_LLM_BASE_URL")
    api_key = os.getenv("AI_ASSISTANTS_EMBEDDINGS_API_KEY") or os.getenv("AI_ASSISTANTS_LLM_API_KEY")
    model = os.getenv("AI_ASSISTANTS_EMBEDDINGS_MODEL")
    if not base_url or not api_key or not model:
        return None
    timeout_raw = os.getenv("AI_ASSISTANTS_EMBEDDINGS_TIMEOUT_SECONDS", "10")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 10.0
    return OpenAICompatibleEmbeddingsConfig(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    )


class OpenAICompatibleEmbeddingsProvider:
    """Embeddings provider calling an OpenAI-compatible /v1/embeddings endpoint."""

    def __init__(self, config: OpenAICompatibleEmbeddingsConfig, client: httpx.Client | None = None) -> None:
        self._config = config
        self._client = client or httpx.Client(timeout=config.timeout_seconds)

    def embed(self, texts: list[str]) -> list[list[float]]:
        url = f"{self._config.base_url}/v1/embeddings"
        resp = self._client.post(
            url,
            headers={"Authorization": f"Bearer {self._config.api_key}"},
            json={"model": self._config.model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, Mapping):
            raise ValueError("Invalid embeddings response")
        items = data.get("data")
        if not isinstance(items, list):
            raise ValueError("Invalid embeddings response: missing data")
        out: list[list[float]] = []
        for item in items:
            if not isinstance(item, Mapping):
                raise ValueError("Invalid embeddings response: item")
            emb = item.get("embedding")
            if not isinstance(emb, list) or any(not isinstance(x, (int, float)) for x in emb):
                raise ValueError("Invalid embeddings response: embedding")
            out.append([float(x) for x in emb])
        return out


def build_embeddings_provider_from_env() -> EmbeddingsProvider | None:
    """Build embeddings provider from env vars, or None if not configured."""
    cfg = load_openai_compatible_embeddings_config()
    if cfg is None:
        return None
    return OpenAICompatibleEmbeddingsProvider(cfg)


