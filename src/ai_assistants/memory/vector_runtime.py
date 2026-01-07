from __future__ import annotations

import os

from ai_assistants.tools.vector_memory_tools import VectorMemoryTools

_tools: VectorMemoryTools | None = None


def _enabled() -> bool:
    raw = os.getenv("AI_ASSISTANTS_VECTOR_MEMORY_ENABLED", "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def get_vector_memory_tools() -> VectorMemoryTools | None:
    """Return VectorMemoryTools if enabled and embeddings are configured."""
    global _tools
    if not _enabled():
        return None
    if _tools is None:
        _tools = VectorMemoryTools.from_env()
    # If embeddings aren't configured, VectorMemoryTools will no-op; still return it.
    return _tools


def set_vector_memory_tools(tools: VectorMemoryTools | None) -> None:
    """Override vector memory tools (tests)."""
    global _tools
    _tools = tools


